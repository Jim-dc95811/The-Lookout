#!/usr/bin/env python3
"""units_kml.py - The Lookout: live units KML server  (Claude + Jim, 2026-11-14)

The second half of the Lookout. bk_bridge.py puts clean NMEA on the network (:10110);
this reads that feed, pairs each position with its unit ID, and serves a live
units.kml on :8080. Any ArcGIS Earth on the LAN opens a NetworkLink to it once and
the units move on their own - no Python, no install on the viewing PC.

It reads the BRIDGE's feed, not the radio, so it never opens a second connection to
the radio and it works with any NMEA source the bridge is serving.

Run (normal):  python3 units_kml.py              # reads the bridge on 127.0.0.1:10110
Run (demo):    python3 units_kml.py --demo        # 3 moving synthetic units, no radio
Stop:          Ctrl+C
Serves:        http://<this-pi>:8080/units.kml
Optional:      aliases.json beside this file = {"7101": "Engine 7", ...}
"""
import re, time, math, json, socket, threading, sys, argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# ---- where we read from / serve to ----
BRIDGE_HOST = "127.0.0.1"     # the bridge's NMEA feed (same Pi)
BRIDGE_PORT = 10110
SERVE_HOST  = "0.0.0.0"       # serve units.kml to the whole LAN
SERVE_PORT  = 8080
STALE_S     = 90             # a unit with no update this long is labelled "stale"
EXPIRE_S    = 7200           # ...and dropped from the map after this long (0 = never)
RECONNECT_S = 4

# ---------- NMEA parser: lifted verbatim from the P25 GPS Tracker (p25_core.py) ----------
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

def _to_deg(value, hemi, deg_digits):
    if not value:
        return None
    try:
        d = int(value[:deg_digits]); m = float(value[deg_digits:])
    except ValueError:
        return None
    dd = d + m / 60.0
    return -dd if hemi in ("S", "W") else dd

def _valid_coord(lat, lon):
    if lat is None or lon is None:
        return False
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return False
    if abs(lat) < 1e-6 and abs(lon) < 1e-6:     # null island = no real fix
        return False
    return True

class Report:
    __slots__ = ("unit", "lat", "lon", "alt", "sats", "utc")
    def __init__(self, unit, lat, lon, alt, sats, utc):
        self.unit, self.lat, self.lon, self.alt, self.sats, self.utc = unit, lat, lon, alt, sats, utc

class StreamParser:
    """Feed raw bytes; yields paired (GGA position + PP25 unit id) Reports."""
    def __init__(self):
        self._buf = bytearray()
        self._pending = None
    def feed(self, data: bytes):
        out = []
        self._buf.extend(data)
        text = self._buf.decode("latin-1")
        last_end = 0
        for m in _SENTENCE.finditer(text):
            s = m.group(0); last_end = m.end()
            if not _nmea_ok(s):
                continue
            f = s.split(",")
            tag = f[0][1:]
            if tag.endswith("GGA") and len(f) >= 10:
                lat = _to_deg(f[2], f[3], 2); lon = _to_deg(f[4], f[5], 3)
                if f[6] in ("", "0") or not _valid_coord(lat, lon):
                    self._pending = None
                    continue
                self._pending = {"lat": lat, "lon": lon, "alt": f[9], "sats": f[7], "utc": f[1]}
            elif tag == "PP25" and len(f) >= 2 and f[1]:
                if self._pending is not None:
                    p = self._pending
                    out.append(Report(f[1], p["lat"], p["lon"], p["alt"], p["sats"], p["utc"]))
                    self._pending = None
        if last_end:
            del self._buf[:last_end]
        if len(self._buf) > 8192:
            del self._buf[:-2048]
        return out

# ---------- live unit state ----------
_units = {}                 # unit id -> dict(lat, lon, alt, sats, utc, seen=monotonic)
_lock = threading.Lock()

def _put(rep):
    with _lock:
        _units[str(rep.unit)] = {"lat": rep.lat, "lon": rep.lon, "alt": rep.alt,
                                 "sats": rep.sats, "utc": rep.utc, "seen": time.monotonic()}

def _aliases():
    try:
        return json.loads(Path(__file__).with_name("aliases.json").read_text())
    except Exception:
        return {}

def _age(sec):
    s = int(sec)
    if s < 60:   return "now"
    if s < 3600: return f"{s // 60} min"
    return f"{s // 3600} h {(s % 3600) // 60:02d} min"

def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_kml():
    al = _aliases(); now = time.monotonic(); marks = []
    with _lock:
        items = list(_units.items())
    for uid, u in items:
        age = now - u["seen"]
        if EXPIRE_S and age > EXPIRE_S:
            continue
        name = al.get(uid, uid)
        stale = "  (stale)" if age > STALE_S else ""
        label = f"{_esc(name)} · {_age(age)}{stale}"
        marks.append(
            f'<Placemark><name>{label}</name>'
            f'<Point><coordinates>{u["lon"]:.6f},{u["lat"]:.6f},0</coordinates></Point></Placemark>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Live units</name>'
            + "".join(marks) + '</Document></kml>').encode("utf-8")

# ---------- HTTP server ----------
class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = build_kml()
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.google-earth.kml+xml")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

# ---------- read the bridge's NMEA feed ----------
def read_bridge():
    while True:
        s = None
        try:
            print(f"[units] connecting to bridge {BRIDGE_HOST}:{BRIDGE_PORT} ...", flush=True)
            s = socket.create_connection((BRIDGE_HOST, BRIDGE_PORT), timeout=6)
            s.settimeout(1.0)
            sp = StreamParser()
            print("[units] reading NMEA from the bridge", flush=True)
            while True:
                try:
                    data = s.recv(65535)
                except socket.timeout:
                    continue
                if not data:
                    print("[units] bridge closed - reconnecting", flush=True)
                    break
                for rep in sp.feed(data):
                    _put(rep)
                    print(f"[units] {rep.unit}  {rep.lat:.5f},{rep.lon:.5f}", flush=True)
        except OSError as e:
            print(f"[units] bridge connection problem: {e} - retrying", flush=True)
        finally:
            if s is not None:
                try: s.close()
                except OSError: pass
        time.sleep(RECONNECT_S)

# ---------- demo feed (no radio): 3 units walking small circles over Bryceville ----------
def demo_feed():
    print("[units] DEMO mode - 3 synthetic units, no radio needed", flush=True)
    base = [("7-01", 30.3961, -81.9392, 0.020, 0.0),
            ("7-02", 30.3850, -81.9100, 0.013, 2.1),
            ("7-03", 30.4050, -81.9600, 0.027, 4.1)]
    t = 0
    while True:
        for uid, clat, clon, r, ph in base:
            a = ph + t * 0.14
            lat = clat + r * math.sin(a)
            lon = clon + r * math.cos(a) / math.cos(math.radians(clat))
            _put(Report(uid, lat, lon, "0", "9", "000000"))
        t += 1
        time.sleep(2)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The Lookout - live units KML server")
    ap.add_argument("--demo", action="store_true", help="serve moving synthetic units, no radio")
    args = ap.parse_args()
    print("=== The Lookout - live units KML server ===", flush=True)
    print(f"serving units.kml on http://{SERVE_HOST}:{SERVE_PORT}/units.kml  (Ctrl+C to stop)", flush=True)
    threading.Thread(target=(demo_feed if args.demo else read_bridge), daemon=True).start()
    try:
        ThreadingHTTPServer((SERVE_HOST, SERVE_PORT), _H).serve_forever()
    except KeyboardInterrupt:
        print("\n[units] stopped.", flush=True)
        sys.exit(0)
