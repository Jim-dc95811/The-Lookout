#!/usr/bin/env python3
"""bk_bridge.py - BK radio GPS -> network NMEA bridge  (Claude + Jim, 2026-11-14)

Turns a Raspberry Pi or OpenWrt router into a field bridge box: it reads the BK base
relay's framed GPS stream over the USB-RNDIS link (10.250.46.6:65535), pulls out the
standard NMEA sentences, and RE-SERVES them as a plain NMEA-over-TCP feed on port 10110
to any number of devices at once - PCs, phones, tablets. Plug the radio in, run this,
and the whole scene can read the same live feed over the network.

The sentence-finder + checksum are lifted verbatim from the proven P25 GPS Tracker
(p25_core.py), which is frame-agnostic: it never needs to decode the 80..81 wrapper,
it just scans the raw bytes for valid $....*cs sentences and verifies each one.

v1.1 (2026-11-15): one stuck/frozen viewer can no longer stall the feed for the others -
each client socket has a send timeout and a viewer that can't keep up is dropped, and
the fan-out no longer holds the lock while sending.

v1.2 (2026-11-15): the bridge now ANNOUNCES its radio link state into the feed, so the
map can raise an immediate alarm when the radio is unplugged instead of letting units
quietly go stale. It emits a $PLKT,LINK,UP / $PLKT,LINK,DOWN heartbeat every few seconds
(and instantly on any change). This is a proprietary NMEA sentence; other NMEA apps
ignore it. All sends still come from this one thread, so nothing interleaves on a socket.

Run:   python3 bk_bridge.py
Stop:  Ctrl+C
"""
import re, socket, threading, time, sys

VERSION = "1.2"

# ---- upstream: the BK base relay ----
RADIO_IP    = "10.250.46.6"
RADIO_PORT  = 65535
SUBSCRIBE   = bytes.fromhex("800418e481")     # the 5-byte subscribe: 80 04 18 e4 81
KEEPALIVE_S = 20                              # re-send subscribe this often
WATCHDOG_S  = 90                              # no bytes at all this long -> reconnect
RECONNECT_S = 4

# ---- downstream: who we serve the NMEA to ----
SERVE_HOST     = "0.0.0.0"                    # all of the box's networks (LAN, etc.)
SERVE_PORT     = 10110                        # the standard NMEA-0183-over-TCP port
HEARTBEAT_S    = 15                           # print an "alive, no fixes yet" line this often
SEND_TIMEOUT_S = 5                            # drop a viewer that can't accept data within this
STATUS_EVERY_S = 5                            # broadcast the LINK UP/DOWN heartbeat this often

# ---- NMEA extraction (verbatim from p25_core.py) ----
_SENTENCE = re.compile(r"\$[^*$\r\n]{2,88}\*[0-9A-Fa-f]{2}")

def _nmea_ok(s):
    body, _, chk = s[1:].partition("*")
    try:
        want = int(chk[:2], 16)
    except ValueError:
        return False
    g = 0
    for c in body:
        g ^= ord(c)
    return g == want

def _mk(body):
    g = 0
    for c in body:
        g ^= ord(c)
    return f"${body}*{g:02X}"

# ---- client fan-out ----
_clients = set()
_lock = threading.Lock()

def _broadcast(sentence):
    data = (sentence + "\r\n").encode("ascii", "replace")
    with _lock:
        clients = list(_clients)             # take a copy, then send WITHOUT holding the lock
    dead = []
    for c in clients:
        try:
            c.sendall(data)                  # socket has a send timeout; a stuck reader raises here
        except OSError:
            dead.append(c)
    if dead:
        with _lock:
            for c in dead:
                _clients.discard(c)
            n = len(_clients)
        for c in dead:
            try: c.close()
            except OSError: pass
        print(f"[bridge] dropped {len(dead)} slow/closed client(s)  (now {n} connected)",
              flush=True)

def _serve_clients():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVE_HOST, SERVE_PORT))
    srv.listen(16)
    print(f"[bridge] serving NMEA on tcp {SERVE_HOST}:{SERVE_PORT} - connect any device here",
          flush=True)
    while True:
        try:
            conn, addr = srv.accept()
        except OSError as e:
            print(f"[bridge] accept error: {e} - continuing", flush=True)
            time.sleep(0.5)
            continue
        conn.settimeout(SEND_TIMEOUT_S)       # a viewer that can't keep up is dropped, not blocked
        with _lock:
            _clients.add(conn)
            n = len(_clients)
        print(f"[bridge] client connected: {addr[0]}:{addr[1]}  (now {n} connected)",
              flush=True)

# ---- radio link status (announced into the feed so the map can alarm) ----
_link_state     = "down"       # "up" once subscribed and reading; "down" while the radio is lost
_last_status_at = 0.0
_printed_state  = None

def _emit_status(now, force=False):
    global _last_status_at, _printed_state
    if force or (now - _last_status_at) >= STATUS_EVERY_S:
        _broadcast(_mk("PLKT,LINK,UP" if _link_state == "up" else "PLKT,LINK,DOWN"))
        _last_status_at = now
    if _printed_state != _link_state:
        print(f"[radio] LINK {_link_state.upper()}", flush=True)
        _printed_state = _link_state

def _set_link(state, now):
    global _link_state
    if _link_state != state:
        _link_state = state
        _emit_status(now, force=True)         # announce the change immediately

def _wait(seconds):
    """Sleep in small steps so the LINK heartbeat keeps going while we are disconnected."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        _emit_status(time.monotonic())
        time.sleep(0.5)

# ---- radio reader ----
def _radio_loop():
    buf = bytearray()
    while True:
        s = None
        try:
            print(f"[radio] connecting to {RADIO_IP}:{RADIO_PORT} ...", flush=True)
            s = socket.create_connection((RADIO_IP, RADIO_PORT), timeout=6)
            s.sendall(SUBSCRIBE)
            s.settimeout(0.5)
            print("[radio] connected + subscribed - listening for GPS", flush=True)
            _set_link("up", time.monotonic())
            last_keep = last_data = last_beat = time.monotonic()
            got_any = False
            while True:
                try:
                    data = s.recv(65535)
                except socket.timeout:
                    data = b""
                now = time.monotonic()
                if data:
                    last_data = now
                    buf.extend(data)
                    text = buf.decode("latin-1")
                    last_end = 0
                    for m in _SENTENCE.finditer(text):
                        sen = m.group(0); last_end = m.end()
                        if _nmea_ok(sen):
                            got_any = True
                            with _lock:
                                n = len(_clients)
                            print(f"[nmea -> {n} client(s)] {sen}", flush=True)
                            _broadcast(sen)
                    if last_end:
                        del buf[:last_end]
                    if len(buf) > 8192:
                        del buf[:-2048]
                if KEEPALIVE_S and now - last_keep > KEEPALIVE_S:
                    try: s.sendall(SUBSCRIBE)
                    except OSError: pass
                    last_keep = now
                _emit_status(now)                       # LINK UP heartbeat
                if not got_any and now - last_beat > HEARTBEAT_S:
                    print("[radio] alive - subscribed and waiting (no units transmitting yet)",
                          flush=True)
                    last_beat = now
                if now - last_data > WATCHDOG_S:
                    print("[radio] no bytes for a while - reconnecting", flush=True)
                    break
        except OSError as e:
            print(f"[radio] connection problem: {e} - retrying", flush=True)
        finally:
            if s is not None:
                try: s.close()
                except OSError: pass
        _set_link("down", time.monotonic())             # radio is gone -> raise the alarm
        _wait(RECONNECT_S)

if __name__ == "__main__":
    print(f"=== BK radio -> NMEA network bridge  v{VERSION} ===", flush=True)
    threading.Thread(target=_serve_clients, daemon=True).start()
    try:
        _radio_loop()
    except KeyboardInterrupt:
        print("\n[bridge] stopped.", flush=True)
        sys.exit(0)
