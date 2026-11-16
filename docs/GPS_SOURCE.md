# The Lookout's own position — a local USB GPS

**New in bk_bridge v1.3 (2026-11-16) — LIVE-PROVEN on a GL-MT6000 router.** The box can now
plot **itself** on the map — a "you are here" — right alongside the radio fleet. Plug a GPS
into the powered USB hub (beside the radio and the SSD) and `bk_bridge.py` reads it in a
separate thread and broadcasts the box's own fix into the same `:10110` feed, tagged as one
reserved unit (`SELF_ID`, default `LOOKOUT`). The map needs no change — the box shows up like
any other unit, and you can give it a friendly name in the Alias Manager.

The radio reader is **byte-for-byte unchanged**. If there is no GPS, nothing changes: the
bridge runs exactly as v1.2's radio-only behaviour.

> **Proven 2026-11-16:** a Garmin GPS 18 USB on the router's hub, read directly over libusb,
> put a `LOOKOUT` dot on the browser map in Bryceville, FL — on the same map as a live P25
> field unit (`9076801`). **2 units, offline, nothing installed on the viewer.**

---

## What GPS can I plug in?

`gps_source.py` finds a GPS three ways and uses the first that gives a real fix:

| # | Source | For | Needs |
|---|---|---|---|
| 1 | **Garmin USB over libusb** `091E:0003` | **Your Garmin GPS 18 USB** — the proven path on the router | `libusb-1.0-0` only (ctypes; no pyusb, no gpsd) |
| 2 | **gpsd** on `127.0.0.1:2947` | A serial puck you'd rather let gpsd manage | `gpsd` installed + pointed at the device |
| 3 | **Serial NMEA** `/dev/ttyUSB*` / `/dev/ttyACM*` | Any plain USB-serial puck (BU-353N5, u-blox, a Garmin in NMEA mode) | `pyserial` + the USB-serial kmod |

Your proven unit is the **Garmin GPS 18 USB (091E:0003)**, which speaks Garmin's own binary
protocol, **not NMEA**. The clean path turned out **not** to be gpsd: on the GL-MT6000's
OpenWrt build, gpsd *detects* the Garmin ("Garmin USB binary") but can't read it (its build
lacks the libusb/non-NMEA read path), and `gpsbabel` isn't packaged. So the Lookout talks the
Garmin's own D800 PVT protocol **directly over libusb** (`garmin_linux.py`, pure ctypes) — the
exact protocol reverse-engineered on Jim's unit, with the USB endpoints discovered from the
device itself. It needs only `opkg install libusb-1.0-0`. That path is tried first and leads;
it fails instantly when no Garmin is plugged in, so it costs nothing on a serial/gpsd rig.

---

## Setup on the router (OpenWrt), one step at a time

First see what the kernel calls your GPS. Plug it into the hub, then:

```
lsusb            # look for "091E:0003 Garmin" (your 18 USB) or a serial chip (CP210x, PL2303, FTDI)
```

### Path 1 — Garmin 18 USB direct over libusb (proven, recommended)
```
opkg update
opkg install libusb-1.0-0        # the only dependency (ctypes talks to it; no pyusb, no gpsd)
rmmod garmin_gps 2>/dev/null     # free the device from the kernel serial driver so libusb can claim it
python3 garmin_linux.py          # standalone test: prints the endpoints it found, then live fixes
```
When `garmin_linux.py` prints `PVT fix=3 lat=.. lon=..` and `$GPGGA/$GPRMC` lines, you're done —
`bk_bridge.py` auto-uses it. (The boot service `rmmod`s `garmin_gps` on every start, so libusb
owns the Garmin after a reboot too.)

### Path 2 — a plain serial NMEA puck
```
# install the driver that matches your chip from lsusb (pick ONE):
opkg install kmod-usb-serial-cp210x     # CP210x (common)
opkg install kmod-usb-serial-pl2303     # Prolific
opkg install kmod-usb-serial-ftdi       # FTDI
opkg install kmod-usb-acm               # cdc-acm (u-blox and others)
opkg install python3-pyserial           # or: pip install pyserial
cat /dev/ttyUSB0                        # should scroll $GPGGA/$GPRMC
```
`bk_bridge.py` then auto-finds it on `/dev/ttyUSB*` / `/dev/ttyACM*`.

### Path 3 — gpsd (for a serial puck you'd rather gpsd manage; NOT the Garmin on this build)
```
opkg update && opkg install gpsd gpsd-clients
gpsd -n -N -D2 /dev/ttyUSB0 &     # test in the foreground first
gpspipe -r -n 5                   # should print live $GPGGA/$GPRMC
```
Note: on the GL-MT6000 build, gpsd can't read the Garmin 18 USB — use Path 1 for that unit.

---

## Name the box on the map

`SELF_ID` (top of `bk_bridge.py`, default `LOOKOUT`) is the unit id the box reports under.
Give it a friendly name like any unit — in the Alias Manager, map `LOOKOUT` → `My Truck`
(or set `SELF_ID` to your own call sign). To turn the feature off, set `GPS_ENABLE = False`.

---

## How it reads the Garmin (for the curious / the next maintainer)

A Garmin USB puck does **not** expose a COM port and does **not** speak NMEA — it speaks
Garmin's binary USB protocol. `garmin_linux.py` talks it directly:

1. Open `091E:0003` with libusb; detach the kernel `garmin_gps` driver; claim interface 0.
2. **Discover the USB endpoints from the device's own config descriptor** (a control transfer),
   rather than hardcoding them — this is what makes it work across units.
3. Send `Start_Session` then `Start_Pvt`; the unit streams D800 PVT records ~1/s on the
   interrupt pipe (read in 64-byte chunks, reassembled until one is < 64).
4. Decode each 64-byte record (`<ffffhdddffffhi>`): lat/lon are **radians** → ×180/π; MSL
   altitude = `alt − msl_hght`.

The packet framing + D800 decode live in `gps_source.py` and are reused verbatim by both the
standalone test and the production reader — one implementation, no duplication.

**The only dependency is `libusb-1.0-0`.** No gpsd, no gpsbabel, no pyusb, no kernel rebuild.
