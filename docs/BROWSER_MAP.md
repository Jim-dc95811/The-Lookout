# The Lookout — Live Map in Any Browser (no app, no internet)

**Proven live 2026-11-15** on a GL-MT6000 router, on a PC and an Android phone, with real P25 units (9076801, 9076803) riding on Bryceville aerial imagery — nothing installed on the viewing devices but a web browser. The same day it went further: the router served a **46 GB Z20 Esri `.tpkx`** — the exact tile package ArcGIS Earth opens, with no conversion — straight off an external SSD, at full Z20 detail and smooth zoom, to a PC and a phone.

This document is the permanent record of what was built, why it matters, and exactly how to stand it up again. Code lives on branch `browser-map-wip` (`units_kml.py` **v1.9** + `map.html` + `leaflet.js` + `leaflet.css`).

---

## 1. What it is, in one line

**The router serves a real slippy map — your own offline map tiles with your live units on top — straight to any device's web browser.** No ArcGIS Earth, no app install, no cloud, no internet.

Put plainly: this is the 2D heart of ArcGIS Earth (an offline multiresolution tile pyramid you can pan and zoom, with a live overlay) running in a plain browser. The tile pyramid is the `.mbtiles` file you already make in QGIS; the pan/zoom engine is Leaflet, the same standard machinery behind every web map. The router wires your pyramid to that engine and draws the live P25 feed on top.

## 2. Why it matters

- **It reaches every device with zero install.** A locked-down, Group-Policy PC with no admin and no Python? It opens a link. A phone or tablet? It opens a link. Same live map on every screen.
- **It fits the mission:** *don't make the user learn GIS before they can use geography.* Nobody installs or learns an app. They open a URL and see the map.
- **It sidesteps ArcGIS Earth mobile's walls entirely.** AE mobile refuses plain `http://`, won't trust a self-signed cert, and only takes URLs from ArcGIS Online / Enterprise — so a self-hosted live LAN feed can't get in. A browser doesn't care. (Full research record: AE mobile was a dead end for a live self-hosted feed; the browser is the answer.)
- **It serves the very tile packages ArcGIS Earth uses — no conversion.** Since v1.9 the router reads tiles straight out of an Esri `.tpkx` (Compact Cache V2, exactly what `mb2tpkx` writes). The map file you already built for ArcGIS Earth *is* the file the browser serves. Proven at 46 GB of Z20 off an SSD (see §7).

What it is **not**: no 3D globe or terrain, no Esri/Living Atlas data ecosystem, no KML authoring. It is 2D tiles + live points. ArcGIS Earth still owns the rest — this is a new, dead-simple *delivery channel*, not a replacement.

**Why it can out-run ArcGIS Earth at this one job.** It isn't magic and it isn't a better GIS — it's doing far less. ArcGIS Earth is a 3D globe: terrain mesh, draping, reprojection, a whole authoring and data ecosystem riding along. The browser map draws 2D raster tiles only — seek to the tile in the package, hand the raw JPEG to Leaflet, draw the units on top. No globe math, no decode-and-recompress, no weight. For the one thing most field users actually need — *look at the map, see the units* — stripping the problem down to its 2D heart is exactly why it flies. Keep ArcGIS Earth for the globe, the KML authoring and the Esri data; this is the delivery truck that reaches the crew who would never open the globe.

## 3. How it works

```
Field units ──P25 GPS over the air──▶ BK M150 base ──USB (RNDIS)──▶ GL-MT6000 router ──LAN──▶ any web browser
                                                                      │ bk_bridge.py  (reads radio, serves NMEA :10110)
                                                                      │ units_kml.py  (:8080):
                                                                      │   /                → map.html (Leaflet page)
                                                                      │   /leaflet.js /leaflet.css  (bundled, local — no CDN)
                                                                      │   /meta.json       → basemap bounds + zoom range
                                                                      │   /tiles/{z}/{x}/{y} → JPEG tiles out of basemap.mbtiles
                                                                      │   /units.json      → live unit positions (polled every 3s)
                                                                      └   basemap.mbtiles  (your QGIS tile pyramid)
```

The browser loads `map.html`, which starts a Leaflet map, adds a raster tile layer pointing at `/tiles/{z}/{x}/{y}` (so Leaflet pulls the right pyramid level as you zoom), and every 3 seconds re-fetches `/units.json` and moves the unit markers. All of it is served by the router; the browser reaches nothing else.

### Key technical facts (don't lose these)
- **The basemap is an MBTiles file** — a SQLite database of pre-rendered map tiles at many zoom levels (a multiresolution pyramid). This is exactly what QGIS exports and what feeds `mb2tpkx`. The router reads tiles out of it directly; no conversion needed.
- **TMS → XYZ row flip.** MBTiles stores tile rows TMS-style (row 0 at the south); Leaflet/XYZ asks with row 0 at the north. The server flips: `tms_row = (2^z − 1) − y`. (This is the same flip `mb2tpkx` already does.)
- **Leaflet 1.9.4 is bundled on the router** (`/leaflet.js`, `/leaflet.css`) and served locally, so the page needs no internet and no CDN.
- **`/meta.json`** hands the page the basemap's `bounds`, `minzoom`, `maxzoom` so the map fits the right area and zoom range automatically.
- **Graceful with no basemap:** if `basemap.mbtiles` is missing, tiles 404 and the units simply draw on a blank background (older behavior).
- **Config:** the basemap defaults to `basemap.tpkx` then `basemap.mbtiles` beside `units_kml.py` (i.e. `/root/…` on the router); override with the `LOOKOUT_MBTILES` environment variable.
- **TPKX is supported too (v1.9).** The server reads tiles straight out of an Esri **`.tpkx`** (Compact Cache V2 — exactly what `mb2tpkx` writes), so it serves the **same tile packages ArcGIS Earth uses, with no conversion**. Backend chosen by extension. Bundle path `tile/L{zz}/R{row:hex}C{col:hex}.bundle`; 8-byte index record = offset (low 40 bits) + size (high bits); row-major; **no TMS flip** (TPKX stores rows north-down already); MIXED JPEG/PNG sniffed per tile. Direct-seek reader, thread-safe, reboot-safe. To use one: put a `.tpkx` on the SSD and symlink `/root/basemap.tpkx` to it.

## 4. How to reproduce it (deploy to a router)

Assumes The Lookout is already installed on the router (bk-bridge + units-kml boot services) and you can `ssh root@192.168.8.1`.

**Step 1 — put a basemap on the router.** Any MBTiles that covers your units' area (made in QGIS). `scp` does **not** work on this router (OpenWrt/dropbear has no sftp-server), so stream it over ssh with `cat`:
```
ssh root@192.168.8.1 "cat > /root/basemap.mbtiles" < "C:\path\to\your map.mbtiles"
```
There's no progress bar; it goes quiet, then returns to the prompt. Verify the size matches the source:
```
ssh root@192.168.8.1 "ls -l /root/basemap.mbtiles"
```

**Step 2 — pull the v1.7 code and restart.**
```
ssh root@192.168.8.1 "cd /root && \
  wget -O units_kml.py https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/browser-map-wip/units_kml.py && \
  wget -O leaflet.js  https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/browser-map-wip/leaflet.js && \
  wget -O leaflet.css https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/browser-map-wip/leaflet.css && \
  wget -O map.html    https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/browser-map-wip/map.html && \
  /etc/init.d/units-kml restart && echo UPDATED"
```

**Step 3 — open it.** In any browser on the router's network:
```
http://192.168.8.1:8080/
```
Type the `http://` on purpose (see gotcha below). You'll see your tiles with the live units on top.

## 5. Gotchas learned the hard way

- **Phone browsers force HTTPS.** Typing `192.168.8.1:8080` gets silently upgraded to `https://…`, which the http-only server can't answer → "refused to connect." Fix: type `http://192.168.8.1:8080/` explicitly, or hand out a **QR code** that encodes the full `http://` URL (recommended for crews — no typing, no upgrade).
- **ArcGIS Earth mobile can't be the client.** It refuses http, won't trust self-signed https, and only accepts ArcGIS Online/Enterprise URLs. The browser is the way in. (AE mobile is still fine as an *offline basemap viewer* for your TPKX.)
- **`scp` fails to the router** (no sftp-server on dropbear). Use `ssh "cat > dest" < localfile`.
- **A basemap only covers its own area.** Units that roam outside the MBTiles bounds land on black. For wider coverage, use a larger map (or multiple). The Bryceville test file covers only `-81.958,30.3838 → -81.9203,30.3961` (zoom 8–20, JPEG).

## 6. Status and what's left

**Status:** `units_kml.py` **v1.9** is LIVE-PROVEN on the GL-MT6000 (2026-11-15) on PC and phone — served from the router's internal flash, from an external SSD, and from both basemap formats: an **MBTiles** pyramid *and* an Esri **`.tpkx`** (the same package ArcGIS Earth opens, no conversion). High-water mark: a **46 GB Z20 `.tpkx`** served off the SSD at full detail and smooth zoom. Code committed and pushed to `browser-map-wip`. Reboot-survival services are in place (v1.8 boot-ordering safety, §7).

**In progress (2026-11-15):** a single whole-area **Z19** package covering a 2°×2° box (≈4 counties) building in QGIS — expected on the order of **100–150 GB**, to be served the same way. When it lands, verify the total file size and that all four corners of the box actually carry imagery (a long, slow basemap fetch can leave edges blank).

**Polish / next (none urgent):**
- Zoom control sits partly under the top header bar — nudge it down.
- Unit labels overlap/clip when two units are very close — offset or collision-handle them.
- **QR code** that opens `http://<router>:8080/` — the right crew-onboarding tool (and it kills the `http://` typing gotcha).
- Fold the basemap step into the setup flow / Lookout Manager so any router is built this way in one shot.
- Bigger / multiple basemaps for wider coverage; a way to pick which map file is active.
- Decide whether to merge `browser-map-wip` into `main` and document it in the main README (this is the "make it official" step).

## 7. Big storage: external SSD on a powered hub (statewide)

The router's internal flash caps the basemap at a few hundred MB. To hold a whole region's Z20 imagery, put the map on an **external SSD** and serve tiles straight off it. **Proven live 2026-11-15** on a Samsung T5 (465 GB), with the radio and the SSD sharing the router's one port through a powered industrial hub — PC and phone, serving entirely off the SSD. The high-water test: a **46 GB Z20 `.tpkx`** (one 1° county) served flawlessly — full Z20 detail *and* a smooth regional zoom-out — straight off the T5.

**Storage math (measured / estimated, honest).** At JPEG q75 these run roughly: **~46 GB per 1° county at Z20** (measured); a 2°×2° area (≈4 counties) ≈ **~100–150 GB at Z19**, ≈ **~600 GB at Z20** (needs a 1 TB drive), ≈ **~40 GB at Z18**. Z19 over the whole area fits the 465 GB T5 with room; Z20 over the whole area does not.

**Hardware**
- **Powered USB hub** on the router's single USB 3.0 port (a USB 2.0 hub is fine — serving map tiles is thousands of tiny random reads, nowhere near USB 2.0's ceiling). It **must be externally powered** — the router's port can't reliably feed a radio *and* a drive. An industrial hub with a 7–24 V terminal block (e.g. StarTech ST4200USBM, ~500 mA/port, 10 W total) lets the whole rig — router, hub, radio, SSD — run off **12 V vehicle power**.
- Radio and SSD both plug into the hub. The radio re-enumerates behind the hub on its own (the `usb0` hotplug handler re-addresses it to `10.250.46.100`).
- Use an **SSD, not a spinning HDD** (spin-up current); a low-power USB SSD (Samsung T5/T7) fits the per-port budget with room.

**Filesystem:** format the SSD **NTFS** (officially supported by GL firmware, handles multi-GB single files — avoid FAT32's 4 GB file limit). exFAT also works on the Flint 2.

**Point the map at the SSD.** GL firmware auto-mounts USB storage under `/tmp/mountd/disk1_part1/` (confirm with `find /tmp/mountd /mnt -iname '*.mbtiles'`). Replace the default basemap path with a symlink to the file on the SSD, then restart:
```
ssh root@192.168.8.1 "rm -f /root/basemap.mbtiles && ln -s '/tmp/mountd/disk1_part1/<your map>.mbtiles' /root/basemap.mbtiles && /etc/init.d/units-kml restart"
```
Nothing else changes — the server just reads a bigger file. Drop your full statewide `.mbtiles` on the SSD and it serves the same way.

**Reboot safety (v1.8).** On a cold boot the map service can start a moment before GL's USB auto-mount finishes. v1.8 handles it: the server never caches a "no basemap" result, and the page keeps polling `/meta.json`, so the map appears the instant the SSD is mounted — no restart, no blank map. Survives a power-cycle in a truck.

---

*Built by Jim Gaddy (concept, direction, field hardware and testing) with Claude (reverse-engineering, server, and this build). Part of the ArcGIS Earth Unlocked project family.*
