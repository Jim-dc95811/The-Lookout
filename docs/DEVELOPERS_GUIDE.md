# The Lookout — Advanced Developer's Guide

Everything you need to **build, reproduce, and verify** a Lookout box: the
hardware and its requirements, where every file lives on the router, and a
set of shell commands to prove each part works — with the result you should
expect. (The friendly, buy-it visual version of the parts list lives in
[the hardware requirements sheet](graphics/lookout_hardware_requirements.pdf);
this guide is the deep reference.)

---

# 1 · Hardware & requirements

Everything is off-the-shelf. You need **one** regular computer to make the
maps and set the box up — then every screen that *views* the map needs
nothing but a browser.

## 1A · The setup & map-making computer  *(you need one, used once)*

| Spec | Detail |
|---|---|
| Operating system | Windows 10 or 11 (64-bit). The map tools and Lookout Manager are Windows programs. |
| Python | 3.9 or newer — free from `python.org` (tick *Add to PATH*). Runs the map tools and Lookout Manager. |
| Memory (RAM) | **8 GB minimum**, 16 GB recommended. Building large map tiles is memory-hungry. |
| Free disk | A few GB for small maps; **tens of GB** for large areas. An SSD makes builds much faster. |
| Its job | Make the `.tpkx` maps, then run Lookout Manager once to set up the router. After that the box runs on its own — this computer isn't needed in the field. |

## 1B · The Lookout box — the field appliance  *(off-the-shelf parts, runs on 12 V)*

| Part | Detail |
|---|---|
| Router | **GL-MT6000 "Flint 2"** (OpenWrt), the proven build, ~$170. Any OpenWrt router *can* work; this is the tested one. Needs the open internet only once, for setup. |
| Powered USB hub | A **powered** USB 3 hub with its own **12 V** input and a dedicated host port. It powers the SSD, GPS and radio together — a metal/industrial hub suits the field. |
| GPS | **Garmin GPS 18x USB** (USB id `091E:0003`) — the "you are here" unit, read over libusb, nothing to install. Other USB GPS types work but need setup — see `docs/GPS_SOURCE.md`. |
| Telemetry radio | A base radio that outputs received unit positions as NMEA over a USB/network link (built and proven on a **BK M150** P25 relay). Any NMEA position source works. |
| SSD (your maps) | A USB 3 portable SSD, **exFAT or ext4** (*not* FAT32 — its 4 GB per-file limit breaks big maps). Size depends on the maps you carry. Copy `.tpkx` files to the drive **root**. |
| Power | 12 V (a truck) for the router and hub. Plug it in and it comes up on its own; it survives a power cut. |

> **First boot: update the firmware before you provision.** A brand-new box can ship with older
> factory firmware and a different kernel than the one everything here was proven against — which
> matters most for the **kernel-matched audio driver** and the built-in USB-net driver that brings
> up the radio link with no install. On the GL dashboard, take the firmware update it offers and
> let it reboot **before** running Lookout Manager. **Proven baseline:** GL firmware **v4.11.0** /
> OpenWrt **21.02-SNAPSHOT** / kernel **5.4.238**. Run current GL stable, and keep this baseline as
> the known-good fallback if a newer firmware ever breaks the audio `kmod` match.

## 1C · Viewing devices — nothing to install  *(any device, offline)*

| | |
|---|---|
| What works | Any device on the router's Wi-Fi or LAN with a modern browser — PC, phone, tablet. Nothing is installed on it. |
| How they view | Open `http://192.168.8.1:8080` — the live map with the fleet and "you are here." Locked-down, Group-Policy PCs are fine: it's just a web page. |
| Optional | ArcGIS Earth (free) on a PC, to consume the units as a live KML layer instead of the browser map. |

## 1D · Browsers & the "not secure" notice  *(this is normal)*

The Lookout serves a plain **http** page on your own private network — on
purpose. It's a local, offline appliance with no internet and no certificate,
so there's nothing to secure a connection *to*. Nothing you open leaves the box.

| | |
|---|---|
| Works in | Chrome, Edge, Firefox, Safari — desktop and mobile. |
| The 2026 change | Chrome and Edge now warn before plain http by default (Chrome 147, Oct 2026). **Local addresses like `192.168.8.1` are exempt**, so the map normally opens with no warning. |
| If you see "Not secure" | It's safe — your own box, offline. Choose *continue / proceed*. No data goes anywhere. |
| Open it this way | Type the address in full with `http://` — `http://192.168.8.1:8080/` — so the bar doesn't auto-upgrade to `https` (phones especially do this). |
| Avoid | Don't turn on a strict "HTTPS-Only mode." If one is on, allow `192.168.8.1` or turn it off while using the map. |

## 1E · Measured footprint on the box  *(bare-box before/after, GL-MT6000, 2026-11-18)*

| | |
|---|---|
| Writable storage | **450.5 MB used of 7.2 GB — 6% full**, 6.7 GB free (provisioned). Stock, before The Lookout: **427.3 MB**. That's the *entire* writable side: OpenWrt, GL's stock extras **and** everything The Lookout adds. (The MT6000's 7.2 GB loop overlay is far bigger than a typical router's ~100 MB.) |
| The Lookout's share | **~23 MB, measured** — same box, stock 427.3 MB → provisioned 450.5 MB. Python is the bulk; the programs, `map.html` and the bundled Leaflet are small. *Leaner than the earlier ~50–70 MB estimate.* |
| Network footprint | **Three application ports added** — 8080 (map), 8081 (audio), 10110 (position feed) — on top of the stock router's own 22/53/80/443 and localhost 3008. (A `dnsmasq` line on the radio-link subnet also appears when the radio is plugged — stock DNS following a new interface, not ours.) |
| Memory (RAM) | **~244 MB used of ~1 GB** (whole system + all three services), **~690 MB available**; stock idle ~225 MB. No swap. |
| Maps | **On the SSD, never the router** — 145.6 GB on a 466 GB drive in the test; the router's flash holds no map data. |
| Takeaway | The appliance runs on a fraction of the box — ~¼ of RAM, 6% of storage, 23 MB of its own — so it won't bog down, and there's room to grow. |

---

# 2 · File layout on the router

Where every Lookout file lives on the GL-MT6000, so you can check a box has
the same pieces in the same places. The maps are **not** here — they live on
the SSD.

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
│   └── logs/                 (runtime) daily track CSVs (track_YYYY-MM-DD.csv)
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

| On the router | From the repo | What it is |
|---|---|---|
| `/root/bk_bridge.py` | `bk_bridge.py` | Radio GPS → clean feed (:10110); adds this box's own GPS |
| `/root/gps_source.py` | `gps_source.py` | Auto-detects the box's own position source |
| `/root/garmin_linux.py` | `garmin_linux.py` | Garmin GPS over libusb (ctypes) |
| `/root/units_kml.py` | `units_kml.py` | Map server: map, live units, tiles (:8080) |
| `/root/lookout_audio.py` | `lookout_audio.py` | Radio audio → browser (:8081) |
| `/root/map.html` | `map.html` | The browser map; served from `/root` by `units_kml.py` |
| `/etc/init.d/bk-bridge` | `openwrt/bk-bridge` | Boot service (START 95) |
| `/etc/init.d/units-kml` | `openwrt/units-kml` | Boot service (START 96) |
| `/etc/init.d/lookout-audio` | `openwrt/lookout-audio` | Boot service (START 97) |
| `/etc/hotplug.d/net/30-lookout-usb0` | `openwrt/hotplug-usb0` | Radio-link hotplug handler |
| `/etc/rc.d/S95…,S96…,S97…` + `K10…` | *(made by `enable`)* | Start/stop symlinks |

**Runtime / optional** (appear as you use it, not in the base copy):
`/root/aliases.json`, `/root/logs/`, `/root/admin_token.txt`.

**Packages (`opkg`, not files you place):** `python3` · `libusb-1.0-0` ·
`kmod-usb-audio` (+ `kmod-sound-core`) · `alsa-utils` (+ `alsa-lib`) — from GL's
own signed, kernel-matched feed, no firmware rebuild. Detail:
[Beyond Factory](The_Lookout_Beyond_Factory.pdf).

---

# 3 · Shell test & diagnostic commands

Run these over SSH on the router (`ssh root@192.168.8.1`). Each shows what it's
for and what a healthy box returns. A quick full sweep: work top to bottom.

## 3A · Services are running

| Command | Purpose | You should get |
|---|---|---|
| `pgrep -f bk_bridge` | Position bridge process up | a PID (a number) |
| `pgrep -f units_kml` | Map server up | a PID |
| `pgrep -f lookout_audio` | Audio streamer up | a PID |
| `ls /etc/rc.d/*bk-bridge /etc/rc.d/*units-kml /etc/rc.d/*lookout-audio` | Services are **boot-enabled** | `S95bk-bridge`, `S96units-kml`, `S97lookout-audio` plus `K10…` stop links |

## 3B · Ports & feeds

| Command | Purpose | You should get |
|---|---|---|
| `netstat -ltn` | All three servers listening | `LISTEN` lines for `:8080` (map), `:8081` (audio), `:10110` (feed) |
| `wget -qO- http://127.0.0.1:8080/maps.json` | Map server answering | JSON listing the maps on your SSD |
| `wget -qO- http://127.0.0.1:8080/units.kml` | Live units layer builds | KML text with your unit placemarks (long output) |
| `nc 127.0.0.1 10110` | The raw position feed (Ctrl-C to stop) | `$GNGGA` + `$PP25` sentences stream — a `LOOKOUT` GGA appears even with no field units |

## 3C · Radio link (the telemetry radio over USB)

| Command | Purpose | You should get |
|---|---|---|
| `cat /sys/class/net/usb0/operstate` | Radio USB-net link is up | `up` |
| `ip addr show usb0` | Radio link is addressed | `inet 10.250.46.100/24` |

## 3D · Audio hardware (the USB sound card)

| Command | Purpose | You should get |
|---|---|---|
| `cat /proc/asound/cards` | Sound card is seen | a `USB Audio` card listed (card 0) |
| `arecord -l` | Capture device present | `card 0 … device 0` |
| `arecord -D plughw:0,0 -f S16_LE -c1 -r16000 -Vmono -d3 /dev/null` | Live audio level (3 s meter) | a VU meter — **idle ~3%**, **transmission ~54%** |

## 3E · GPS (the box's own "you are here")

| Command | Purpose | You should get |
|---|---|---|
| `python3 /root/garmin_linux.py` | Read the Garmin over libusb | `fix=3 lat=… lon=…` lines (needs sky view) |
| `lsusb` | Garmin enumerated *(if `usbutils` installed)* | a line with `091e:0003` Garmin |

## 3F · Maps / SSD

| Command | Purpose | You should get |
|---|---|---|
| `df -h` | SSD is mounted (and storage headroom) | a `/tmp/mountd/…` line with your drive's size, plus the 6%-used overlay |
| `ls /tmp/mountd/*/` | Maps are on the drive | your `.tpkx` / `.mbtiles` files at the root |

## 3G · Resources & logs

| Command | Purpose | You should get |
|---|---|---|
| `cat /etc/glversion; uname -r` | Firmware & kernel version | GL version (proven **4.11.0**) and kernel (**5.4.238**) |
| `df -h` | Storage headroom | overlay ~6% used, 6.7 GB free |
| `free -h` | RAM headroom | ~1 GB total, a few hundred MB used |
| `logread -e bk_bridge` | Bridge log | `connected + subscribed`, steady heartbeats |
| `logread -e units` | Map server log | serving `units.kml` / tile requests |
| `opkg list-installed` | Dependencies installed | includes `python3`, `libusb-1.0-0`, `kmod-usb-audio`, `alsa-utils`, `alsa-lib` |

**Reading the result:** all three PIDs present + three `LISTEN` ports +
`usb0 up` + a sound card + the SSD mounted = a fully healthy box. A missing
piece points straight at what to fix — no service PID means a program didn't
start (check `logread`); no `S9x` symlink means it was copied but not
`enable`d; no `usb0` means the radio link is down; no sound card means
`kmod-usb-audio` isn't loaded or the card is unplugged.

---

*The Lookout · part of the ArcGIS Earth Unlocked project family · free &
open-source (MIT) · github.com/Jim-dc95811/The-Lookout · Pair with the install
pictogram (box-to-live-map) and `DEPLOY.md`.*
