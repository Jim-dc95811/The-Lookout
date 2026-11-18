# The Lookout — File Layout on the Router

Where every Lookout file lives on the GL-MT6000 (OpenWrt), so you can check,
file by file, that a box has the same pieces in the same places. This is the
reference; the real box should match it. (The maps are **not** here — they
live on the SSD, off the router.)

## The tree

```
Router filesystem  (GL-MT6000, OpenWrt)
│
├── /root/                            ← the programs (copied here, run from here)
│   ├── bk_bridge.py                  radio → clean position feed on :10110 (+ this box's own GPS)
│   ├── gps_source.py                 picks the box's GPS source (Garmin → gpsd → serial NMEA)
│   ├── garmin_linux.py               reads a Garmin GPS over libusb, pure ctypes
│   ├── units_kml.py                  the map server: map + live units + tiles, on :8080
│   ├── lookout_audio.py              radio audio → browser, on :8081
│   ├── map.html                      the browser map (Leaflet bundled inside — no internet)
│   │
│   ├── aliases.json          (runtime) unit ID → friendly name — appears when you name a unit
│   ├── admin_token.txt       (optional) guards unit-renaming; default token if absent
│   └── logs/                 (runtime) daily track CSVs land here (track_YYYY-MM-DD.csv)
│
├── /etc/init.d/                      ← boot services (start the programs at power-on)
│   ├── bk-bridge                     starts bk_bridge.py      (START 95)
│   ├── units-kml                     starts units_kml.py      (START 96)
│   └── lookout-audio                 starts lookout_audio.py  (START 97)
│
├── /etc/rc.d/                        ← enable symlinks (made by `/etc/init.d/<name> enable`)
│   ├── S95bk-bridge   → ../init.d/bk-bridge
│   ├── S96units-kml   → ../init.d/units-kml
│   ├── S97lookout-audio → ../init.d/lookout-audio
│   └── K10bk-bridge, K10units-kml, K10lookout-audio   (matching stop symlinks)
│
├── /etc/hotplug.d/net/
│   └── 30-lookout-usb0               re-addresses the radio link if it's plugged in after boot
│
└── /tmp/mountd/disk1_part1/          ← the SSD mount (name varies) — YOUR MAPS, not on the router
    ├── a_<your-map>.tpkx             .tpkx and/or .mbtiles at the drive ROOT
    ├── b_<another-map>.mbtiles       (name a_ / 1_ to set which opens first; alphabetical)
    └── …
```

## File-by-file

| On the router | From the repo | What it is |
|---|---|---|
| `/root/bk_bridge.py` | `bk_bridge.py` | Reads the radio's GPS, serves a clean position feed (:10110); adds this box's own GPS |
| `/root/gps_source.py` | `gps_source.py` | Auto-detects the box's own position source |
| `/root/garmin_linux.py` | `garmin_linux.py` | Garmin GPS over libusb (ctypes) |
| `/root/units_kml.py` | `units_kml.py` | Map server: map, live units, tiles (:8080) |
| `/root/lookout_audio.py` | `lookout_audio.py` | Radio audio → browser (:8081) |
| `/root/map.html` | `map.html` | The browser map (Leaflet bundled) — served from `/root` by `units_kml.py` |
| `/etc/init.d/bk-bridge` | `openwrt/bk-bridge` | Boot service (START 95) |
| `/etc/init.d/units-kml` | `openwrt/units-kml` | Boot service (START 96) |
| `/etc/init.d/lookout-audio` | `openwrt/lookout-audio` | Boot service (START 97) |
| `/etc/hotplug.d/net/30-lookout-usb0` | `openwrt/hotplug-usb0` | Radio-link hotplug handler |
| `/etc/rc.d/S95…,S96…,S97…` + `K10…` | *(made by `enable`)* | Start/stop symlinks |

**Runtime / optional** (not part of the base copy — they appear as you use it):
`/root/aliases.json` (created when you name a unit), `/root/logs/` (daily track CSVs),
`/root/admin_token.txt` (only if you set a custom rename token).

## Packages installed (not files you place — `opkg` dependencies)

`python3` · `libusb-1.0-0` · `kmod-usb-audio` (+ `kmod-sound-core`) · `alsa-utils` (+ `alsa-lib`)

Pulled from GL's own signed, kernel-matched feed — no firmware rebuild. Full
detail: [The Lookout — Beyond Factory](The_Lookout_Beyond_Factory.pdf).

## Check a real box against this

On the router (over SSH), these two commands list the core files and the
enable symlinks so you can compare to the tree above:

```
ls -la /root/*.py /root/map.html /etc/init.d/bk-bridge /etc/init.d/units-kml /etc/init.d/lookout-audio /etc/hotplug.d/net/30-lookout-usb0
ls /etc/rc.d/ | grep -E 'bk-bridge|units-kml|lookout-audio'
```

Everything in the tree except the `(runtime)` / `(optional)` items should be
present. If a boot service is missing from `/etc/rc.d/`, it was copied but not
`enable`d. (Lookout Manager places and enables all of this for you in one
click — this page is for verifying or doing it by hand.)
