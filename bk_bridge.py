#!/usr/bin/env python3
"""bk_bridge.py - BK radio GPS -> network NMEA bridge  (Claude + Jim, 2026-11-14)

Turns a Raspberry Pi into a field bridge box: it reads the BK base relay's framed
GPS stream over the USB-RNDIS link (10.250.46.6:65535), pulls out the standard NMEA
sentences, and RE-SERVES them as a plain NMEA-over-TCP feed on port 10110 to any
number of devices at once - PCs, phones, tablets. Plug the radio into the Pi, run
this, and the whole scene can read the same live feed over the network.

The sentence-finder + checksum are lifted verbatim from the proven P25 GPS Tracker
(p25_core.py), which is frame-agnostic: it never needs to decode the 80..81 wrapper,
it just scans the raw bytes for valid $....*cs sentences and verifies each one.

Run:   python3 bk_bridge.py
Stop:  Ctrl+C
"""
import re, socket, threading, time, sys

# ---- upstream: the BK base relay ----
RADIO_IP    = "10.250.46.6"
RADIO_PORT  = 65535
SUBSCRIBE   = bytes.fromhex("800418e481")     # the 5-byte subscribe: 80 04 18 e4 81
KEEPALIVE_S = 20                              # re-send subscribe this often
WATCHDOG_S  = 90                              # no bytes at all this long -> reconnect
RECONNECT_S = 4

# ---- downstream: who we serve the NMEA to ----
SERVE_HOST  = "0.0.0.0"                       # all of the Pi's networks (LAN, etc.)
SERVE_PORT  = 10110                           # the standard NMEA-0183-over-TCP port
HEARTBEAT_S = 15                              # print an "alive, no fixes yet" line this often

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

# ---- client fan-out ----
_clients = set()
_lock = threading.Lock()

def _broadcast(sentence):
    data = (sentence + "\r\n").encode("ascii", "replace")
    dead = []
    with _lock:
        for c in list(_clients):
            try:
                c.sendall(data)
            except OSError:
                dead.append(c)
        for c in dead:
            _clients.discard(c)
            try: c.close()
            except OSError: pass

def _serve_clients():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVE_HOST, SERVE_PORT))
    srv.listen(16)
    print(f"[bridge] serving NMEA on tcp {SERVE_HOST}:{SERVE_PORT} - connect any device here",
          flush=True)
    while True:
        conn, addr = srv.accept()
        with _lock:
            _clients.add(conn)
        print(f"[bridge] client connected: {addr[0]}:{addr[1]}  (now {len(_clients)} connected)",
              flush=True)

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
        time.sleep(RECONNECT_S)

if __name__ == "__main__":
    print("=== BK radio -> NMEA network bridge ===", flush=True)
    threading.Thread(target=_serve_clients, daemon=True).start()
    try:
        _radio_loop()
    except KeyboardInterrupt:
        print("\n[bridge] stopped.", flush=True)
        sys.exit(0)
