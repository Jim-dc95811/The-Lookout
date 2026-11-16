# Reading a Garmin GPS 18x over libusb on an OpenWrt router

### How *The Lookout* puts a live "you are here" on an offline map — when gpsd and GPSBabel both say no

**Project:** The Lookout (part of the ArcGIS Earth Unlocked family) · **Author:** Jim Gaddy, with Claude (Anthropic) · **Date:** 16 November 2026 · **License:** MIT

---

## Who this is for

- **GIS / public-safety field-mapping people** — you want live unit positions *and* the viewer's own position on an **offline** basemap, on devices that can't install anything. This is how we got the viewer's own GPS onto that map on a $170 router.
- **GL.iNet / OpenWrt users** — what actually works on a GL-MT6000 (Flint 2) when you plug a GPS into it, and the package reality behind it.
- **Garmin-protocol spelunkers** — a complete, working account of the Garmin GPS 18x USB binary protocol read over **libusb-1.0 in pure Python ctypes**, including the two traps that silently break it.
- **Future Claudes (and any coding agent)** — the decision tree, the dead ends, and *why* we took the path we took. The "don't try this" boxes are for you most of all.

Everything here was reverse-engineered and proven on real hardware in one afternoon. Where a path *fails*, it's marked. Where a number matters, it's exact.

---

## 1. The result, up front

A **GL-MT6000 travel router** running OpenWrt reads a **Garmin GPS 18x USB** plugged into its USB hub and plots the box's **own position** on a live map — in a plain web browser, over an offline tile pyramid, with a real P25 radio-telemetry unit riding on the same map. Nothing is installed on the viewing device. It survives a cold power-cut and comes back on its own.

![The Lookout's own position (LOOKOUT) and a live P25 field unit (9076801), both served off a GL-MT6000 after a cold boot, on an offline aerial basemap — Bryceville, FL.](../images/self_position_proof.jpg)

The only dependency added to the router is **`libusb-1.0-0`**. No gpsd, no GPSBabel, no pyusb, no kernel rebuild, no cross-compiler.

```
Garmin GPS 18x ──libusb/ctypes──▶  bk_bridge.py ──NMEA/TCP :10110──▶  units_kml.py ──HTTP :8080──▶  browser / phone / ArcGIS Earth
P25 base radio ─────USB/NMEA──────▶     (one feed, radio units + the box's own "LOOKOUT" unit)
```

The interesting part is the first arrow. A Garmin USB puck is not what it looks like, and the "obvious" ways to read it on a router do not work. This paper is mostly about that arrow.

---

## 2. The trap: a Garmin USB GPS is not a serial NMEA device

Plug a generic USB GPS into a Linux box and you usually get a `/dev/ttyUSB0` that spits `$GPGGA`/`$GPRMC` at 4800 or 9600 baud. Point anything at it and you're done.

**A Garmin USB puck does not do this.** The Garmin GPS 18x USB (USB id `091E:0003`) speaks **Garmin's own binary "Garmin Device Interface" protocol**, not NMEA, and not over a serial tty in any useful way. On Linux the in-kernel `garmin_gps` driver *does* bind it and *does* create a `/dev/ttyUSB*`, which is exactly the trap — the node exists, so you assume it's a serial GPS, but in its default (binary) mode nothing meaningful comes out of that node.

> **⚠ BTW — don't `cat /dev/ttyUSB*` and wait for NMEA.** On our unit that returns **zero bytes**. The kernel `garmin_gps` tty is not a serial NMEA stream; it's a thin shim over Garmin's packet protocol, and it stays silent until something speaks that protocol to it. A silent tty here means "wrong protocol," not "no fix."

So the real task is: **speak Garmin's binary protocol to a `091E:0003` device, on an ARM OpenWrt router, with whatever is installable from `opkg`.** That constraint is what killed every "standard" option.

---

## 3. The dead ends — and exactly why each one failed

We tried the known-good tools first (search before science-lab). Here is each, and why it did not survive contact with a GL-MT6000.

### 3.1 gpsd — recognizes the device, reads nothing

gpsd is *the* Linux GPS daemon and it has a mature Garmin-binary driver. On the router it even **identifies the device correctly**:

```
gpsd: DEVICES → {"class":"DEVICE","driver":"Garmin USB binary", ...}
```

…and then produces **no `TPV`, no `SKY`, no position — ever.** `gpspipe -w` sits empty. The driver name is printed from a USB-id match; actually *reading* the device requires gpsd to have been built with its libusb/non-NMEA code path (`HAVE_LIBUSB` / the non-NMEA0183 drivers). The stock OpenWrt `gpsd` package is not built that way, so it binds the name but has no transport to pull bytes. You get a daemon that is confidently connected to a device it cannot read.

> **⚠ BTW — don't trust "driver: Garmin USB binary" from gpsd on a stock OpenWrt image.** Naming the driver and reading the device are two different capabilities. If `gpspipe` is empty while the device is "recognized," the gpsd build is missing the USB read path. On a general-purpose distro gpsd is the right answer; on a trimmed router image it is a decoy.

### 3.2 GPSBabel — the canonical fix, not packaged

The textbook way to talk to a Garmin USB on Linux is **GPSBabel** (`garmin` format, `usb:` device). Its `jeeps`/`gpsusb` layer does exactly the USB protocol we need. But:

```
opkg install gpsbabel  →  not found
```

It simply isn't in the OpenWrt/`fw.gl-inet.com` feeds for this target, and cross-compiling a C package onto a locked-down field router is the opposite of the "no install, freeze the firmware" goal.

> **⚠ BTW — don't plan a router deployment around GPSBabel.** It's the correct tool on a workstation, but it is not in the OpenWrt package feeds for ARM targets like the MT7986. If your plan's success depends on `opkg install gpsbabel`, your plan has already failed — check the feed first.

### 3.3 pyusb — also not packaged, also fragile

The clean Python route would be **pyusb** (`usb.core.find(...)`). But `python3-pyusb` isn't in the feed either, and `pip install pyusb` on a router with a trimmed Python is a coin-flip that adds a moving part to a box you want frozen.

> **⚠ BTW — on a field router, "`pip install` it" is not a plan.** Every PyPI dependency is something that has to resolve, compile, and keep working offline forever. Prefer what `opkg` already carries.

### 3.4 What *is* installable

One thing that matters **is** in the feed:

```
opkg install libusb-1.0-0     →  installs cleanly (provides libusb-1.0.so.0)
```

And `ctypes` is in the Python standard library, always. That pairing — **a C library we can load + a stdlib FFI** — is the whole key. We don't need pyusb or GPSBabel; we can call `libusb` directly from Python and speak the Garmin protocol ourselves. No compiler, no extra package, nothing to break on reboot.

---

## 4. The Garmin GPS 18x USB protocol, in full

This is the part worth keeping. The protocol below was first reverse-engineered on Windows (via `DeviceIoControl` IOCTLs) for a separate tool and is **cross-platform** — only the USB transport changes. Here it runs on Linux over `libusb_bulk_transfer` / `libusb_interrupt_transfer`. References at the end.

### 4.1 Open and claim

1. `libusb_init`, then `libusb_open_device_with_vid_pid(ctx, 0x091E, 0x0003)`.
2. If the kernel `garmin_gps` driver is attached, **detach it** (`libusb_detach_kernel_driver`) — or `rmmod garmin_gps` first (what we do at boot). You cannot claim an interface the kernel still owns.
3. `libusb_claim_interface(h, 0)`.

> **⚠ BTW — don't leave `garmin_gps` bound and expect libusb to work.** If the kernel driver holds interface 0, your claim fails (or the first transfer does). `rmmod garmin_gps` (persisted at boot) is the clean fix; auto-detach alone is not always enough on OpenWrt.

### 4.2 Find the endpoints — **do not hardcode them**

Every Garmin-USB example hardcodes bulk-OUT `0x02` / interrupt-IN `0x81`. We did too, at first. On our GPS 18x the very first bulk write to `0x02` failed:

```
OPEN FAILED: bulk write to EP 0x02 rc=-1      (LIBUSB_ERROR_IO)
```

The fix — and the single most important lesson in this document — is to **ask the device what its endpoints are** instead of trusting a number from a spec or another unit. Read the configuration descriptor with a control transfer and walk it:

```
libusb_control_transfer(h,
    0x80,      # bmRequestType: device→host, standard, device
    0x06,      # bRequest: GET_DESCRIPTOR
    0x0200,    # wValue: (CONFIG descriptor << 8) | index 0
    0x0000,    # wIndex
    buf, 255, timeout)
```

Then scan the returned bytes for ENDPOINT descriptors (`bDescriptorType == 0x05`) and classify each by `bmAttributes & 0x03` (`2` = bulk, `3` = interrupt) and direction (`bEndpointAddress & 0x80` → IN). Take the OUT endpoint for commands, the interrupt-IN for the PVT stream (fall back to a bulk-IN if there's no interrupt-IN). Use the transfer type the descriptor reports — `bulk` vs `interrupt` — not the one you assumed.

With discovery in place, the same code that failed on `0x02` worked on the first try and printed live fixes.

> **⚠ BTW — never hardcode USB endpoint addresses or transfer types for a HID-ish device.** `0x02`/`0x81` is folklore, not a contract. Units, revisions, and interfaces differ; a wrong address or a bulk-vs-interrupt mismatch returns `LIBUSB_ERROR_IO (-1)` with no hint. Discovery is ~15 lines and it is the difference between "works on my puck" and "works."

### 4.3 Packet framing

Every Garmin packet is a **12-byte header + payload**:

| Field | Offset | Type | Meaning |
|---|---|---|---|
| packet type | 0 | `uint8` | protocol layer: `0` = transport, `20` = application |
| (reserved) | 1–3 | — | zero |
| packet id | 4 | `uint16` LE | message id within the layer |
| (reserved) | 6–7 | — | zero |
| data size | 8 | `uint32` LE | payload length |
| payload | 12 | — | `data size` bytes |

In Python: `struct.pack("<B3xH2xI", ptype, pid, len(data)) + data`.

### 4.4 Handshake and "start streaming"

```
→  (type 0  transport,   id 5  Start_Session)
←  (type 0  transport,   id 6  Session_Started)            # 4-byte unit id in payload
→  (type 20 application,  id 10 Command_Data, data=<H>49)  # 49 = Start_Pvt_Data
←  (type 20 application,  id 51 Pvt_Data)  ~1 Hz, on its own
```

To stop, send `Command_Data` with `50` (`Stop_Pvt_Data`).

### 4.5 The reassembly trap (this one is silent and nasty)

The PVT record arrives on the **interrupt pipe as a 64-byte chunk followed by a shorter (<64) chunk** — classic USB max-packet-size framing. You **must loop reads of 64 bytes and concatenate until a read returns fewer than 64**:

```python
out = b""
while True:
    chunk = interrupt_read(ep_in, 64)   # one USB packet
    out += chunk
    if len(chunk) < 64:
        break                           # short packet = end of record
```

A single 64-byte read returns a **truncated record** — and because latitude sits before longitude in the struct, the quiet failure mode is "latitude looks fine, longitude is garbage or zero." You'll chase a phantom data bug for an hour.

> **⚠ BTW — don't do one fixed-size read for a Garmin PVT record.** It spans multiple USB packets. Reassemble until a short packet. The truncation is silent and it eats longitude first. (A record that is an exact multiple of 64 is terminated by a zero-length packet — the same loop handles it.)

### 4.6 Decoding the D800 PVT record (64 bytes)

```
struct "<ffffhdddffffhi>"  →
  alt, epe, eph, epv   : float32   (metres, error estimates)
  fix                  : int16     (0/1 = none, 2 = 2D, 3 = 3D, 4/5 = differential)
  tow                  : float64   (GPS time of week, seconds)
  lat, lon             : float64   ← RADIANS; multiply by 180/π for degrees
  east, north, up      : float32   (velocity, m/s)
  msl_hght             : float64*  (geoid separation, metres)   [see note]
  leap                 : int16
  wn                   : int32     (GPS week number)
```

Two decode traps worth stating plainly:

- **`lat`/`lon` are in radians.** Multiply by `180/π`. If your position is near (0.5, −1.4) instead of (30.4, −81.9), you forgot this.
- **`alt` is above the ellipsoid; MSL = `alt − msl_hght`.** `msl_hght` is the geoid separation (≈ −31 m in NE Florida), *not* the altitude. Confusing the two puts you tens of metres off vertically and makes the sign look wrong.

> **⚠ BTW — `lat`/`lon` radians and `alt − msl_hght` are the two decode mistakes everyone makes.** Neither throws an error; both just give subtly wrong numbers. Validate against a known location on the first fix.

On our unit the standalone reader printed, within a second of `Start_Pvt`:

```
[garmin] endpoints found: OUT=0x.. IN=0x..
[garmin] PVT fix=3 lat=30.39382 lon=-81.93785
```

— a 3-D fix, dead on the test location. The protocol was proven; everything after was plumbing.

---

## 5. Making it a field appliance (the GL-MT6000 / OpenWrt side)

The reader is `garmin_linux.py` — pure ctypes, no third-party Python. It is tried **first** by an auto-detector (`gps_source.py`) that also knows how to fall back to gpsd or a plain serial NMEA puck; the Garmin path fails instantly when no Garmin is present, so it costs nothing on other rigs. The bridge (`bk_bridge.py`) reads the box's own GPS in a daemon thread and broadcasts its fix into the same NMEA-over-TCP feed as the radio fleet, tagged as one reserved unit (`LOOKOUT`). The radio path is byte-for-byte unchanged; with no GPS the whole feature is a no-op.

To survive a reboot, two things matter on OpenWrt:

1. **Install once:** `opkg install python3 libusb-1.0-0`. After this the router never needs the open internet again — freeze the firmware.
2. **Free the device at boot:** the `procd` init script `rmmod garmin_gps` before launching the bridge, so libusb can claim the Garmin on every power-up. (`procd_set_param respawn` restarts the service if it ever dies.)

We proved the whole thing with a **true cold power-pull**: both services came back with new PIDs, libusb re-claimed the Garmin, and both the box and a live field unit reappeared on the map — nobody at a keyboard.

> **⚠ BTW — when you cut over from a hand-run to the boot service, kill the hand-started processes first.** We left a manually-started map server holding TCP `:8080`; the boot service then crash-looped on `OSError: [Errno 98] Address in use`, and the orphan — having lost its own feed — sat there serving a stale "link down" page. Nothing was wrong with the code. A cold boot clears all orphans, which is one more reason the reboot test is the real acceptance test.

---

## 6. Why this matters for GIS

The payoff is mundane and large: **a viewer that can't install anything still sees live positions on an offline map.** A locked-down, Group-Policy-managed PC, a phone, a tablet — each just opens `http://<router>:8080/`. The router holds the offline tiles (an `.mbtiles` pyramid *or* an Esri `.tpkx` — the exact Compact Cache V2 package ArcGIS Earth opens) and draws the live units on top, with the viewer's own GPS now among them.

A practical note for anyone building the same thing: **deploy your basemaps as `.tpkx`, not MBTiles.** In our server the TPKX reader is pure file-seek into the cache bundles (standard library only — no `sqlite3`, which is a *separate* `opkg` package on OpenWrt), it opens the package once and caches it, and the *same* `.tpkx` serves both the browser map and ArcGIS Earth. MBTiles works, but it adds a dependency, opens a fresh DB connection per tile, and only the browser can read it.

---

## 7. For future Claudes: the method, not just the answer

Five things did the real work here, and they generalize:

1. **Search before science-lab.** The instinct was to start hand-rolling a reader. Searching first turned up *why* gpsd fails on OpenWrt and *that* GPSBabel isn't packaged — which is what pointed at "libusb + ctypes" as the only sane path. An hour of reading saved a day of flailing.
2. **Let the device tell you about itself.** The endpoint-discovery fix is the whole paper in miniature: a hardcoded constant from a spec is a guess; a value read from the descriptor is a fact. Prefer facts you can read at runtime over constants you copied.
3. **Test the logic where it's cheap, prove the transport where it's real.** The D800 decode, the NMEA builders, and the packet framing were all validated in a sandbox against synthetic bytes before touching hardware. Only the one thing that *can't* be faked — the live USB read — waited for the real puck.
4. **Verify every step before building on it.** Each rung (ping the device, claim it, discover endpoints, one fix, the full stack, the boot service, the cold reboot) was confirmed before the next. The bugs that did appear (`rc=-1`, the port conflict) were caught at the rung they happened on, not three layers up.
5. **One step at a time with the human in the loop.** The hardware was on the other end of an SSH session we couldn't see. Giving one command, reading the real output, then giving the next — rather than a wall of steps — is what turned "it doesn't work" into an exact failure line we could fix.

The anti-lesson is worth stating too: **don't accept "the standard tool recognizes it" as "the standard tool reads it."** gpsd naming the Garmin driver while serving nothing is the trap that sends you in circles. Check the actual bytes.

---

## 8. Reference

- **Code:** `garmin_linux.py` (the ctypes/libusb reader + a standalone verbose test), `gps_source.py` (auto-detect + the shared D800 decode and NMEA builders), `bk_bridge.py` (the feed). In the [The-Lookout](https://github.com/Jim-dc95811/The-Lookout) repo, MIT.
- **Setup:** [docs/GPS_SOURCE.md](GPS_SOURCE.md) — install, the gpsd gotcha, and how the reader works.
- **Hardware proven:** GL-MT6000 (Flint 2), OpenWrt 21.02-SNAPSHOT, MediaTek MT7986, 1 GB RAM; Garmin GPS 18x USB (`091E:0003`).
- **Protocol sources:** GPSBabel `jeeps`/`gpsusbwin.c` (the Windows IOCTL numbers and the interrupt-reassembly rule); the Garmin *Device Interface Specification* (protocols A010 link, A800 PVT, data type D800). Nothing is decrypted; the device is only ever read.
- **libusb error codes seen:** `LIBUSB_ERROR_IO = -1`, `LIBUSB_ERROR_TIMEOUT = -7`.

---

*Built in the open so anyone can do the same with their own radio, their own GPS, and their own router. — Jim Gaddy & Claude, 2026-11-16*
