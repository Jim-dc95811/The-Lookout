# CLAUDE.md — The Lookout

**Written by Claude, for Claude.** If you're resuming or picking up The Lookout, read this first — it's the fastest way to get oriented *without* slopping back through everything a past you already learned the hard way. Keep it decodable by a future Claude (possibly a different model) reading it cold: shorthand is fine if it's self-explaining; no private cipher.

> **This repo is public. Keep this file public-safe** — strip any employer/agency names (Jim's own name and GitHub handle are fine; he's an open book). **Precedence:** the live code wins over any prose here; the **family continuity file** (`CLAUDE.md` in the `ArcGIS-Earth-Unlocked` repo) is the highest-authority *newest* cross-family state and owner working-rules; **this** file is the Lookout-focused orientation — current state, the landmines, and the map to the deep docs. Disagreement → trust live code, then the family file, then this.

---

## Current state  *(update this when it changes)*

**2026-11-21 — THE LOOKOUT TRAVELER: GPS chain PROVEN on the MT3000 (first bench, in progress).** The Traveler — a **man-packable, battery GL-MT3000** build (one person on foot, one incident) vs the fixed Lookout (MT6000, vehicle/mains) — reached first bench. **Canonical doc: [`docs/TRAVELER.md`](docs/TRAVELER.md) — read it first for any Traveler work** (platform decision, hardware, power, the two physical configs, software deltas, build order, and the 2026-11-21 BENCH RESULTS block). **Proven today end to end (live hands-on with Jim):** a **VK172 u-blox-7 USB GPS** on a powered SABRENT hub → MT3000 → `cdc-acm` → `/dev/ttyACM0` → **live 3D fix** (Nassau County, 6 sats, HDOP 1.35). Key finds: carton firmware **GL v4.11.0 / kernel 5.4.211** (same generation as the 6000; a different point release than 5.4.238, immaterial — GL's feed is kernel-matched and the Traveler has no audio); **`kmod-usb-acm` ships in the carton firmware**, so the GPS costs **ZERO internet** — it only needed `modprobe cdc-acm` (⚠ **not** auto-loaded at boot, so the init step must load it or a rebooted Traveler has no GPS node); the serial GPS lands on `gps_source.py`'s **third branch** (`SerialSource`, needs `python3-pyserial`). **The one internet-once need is `python3 + python3-pyserial`** — then offline forever. **Still open on the bench:** serve the map (fetch `bk_bridge`/`units_kml`/`gps_source`/`map.html`+leaflet, run the two services), the friendly-address recipe (`a.lan` short-name + port-flip :80↔:8080 + matching SSID, all via `uci` not LuCI), the battery-saving wired config (Wi-Fi off + USB-C→Ethernet = `eth0`), runtime, two-thumbdrive split. **Traveler ≠ fixed Lookout:** **no audio**, **no map menu**, a **locked synced split-screen** (hybrid | street, "you are here" centered in both; canonical pairing Mega 4 grid Z18 hybrid | Z18 street) as its distinct identity — build it as a **mode** on the one shared `units_kml`/`map.html`, don't fork. **Lookout Manager:** the Traveler is being proven **by hand**; a Manager **"Traveler mode"** (skip audio, weld the split view, set up pyserial + cdc-acm-on-boot, apply the name/SSID) comes AFTER the manual recipe is solid — don't build Manager support on guesses. **Any-browser-any-device** display principle holds (PROVEN on an Amazon Fire HD 10, Wi-Fi-only/no-LTE/no-GPS, showing the box's own `LOOKOUT` fix — which is *why* the box keeps its own GPS puck).

**2026-11-18 — SHIPPED + PROVEN out-of-the-box, incl. a GitHub-free install.** The full one-click setup (map + units + "you are here" + audio) was proven **end-to-end from a bare factory GL-MT6000**: Lookout Manager **v2.2**, one button → a live Z20 browser map, two units moving, radio audio playing, on carton-fresh hardware. Measured: the whole appliance adds **~23 MB** to a stock box and **three application ports** (8080/8081/10110). Reboot-survival proven (procd + `sync`). **Then Manager v2.3→v2.4 added a "Use local files" setup mode** (the 12 Lookout files bundled in the package, so the install doesn't need GitHub; opkg packages still come from GL's feed). v2.3 shipped them over **SFTP and crashed** on a real box (`EOF during negotiation`) — the router's **dropbear SSH has no SFTP subsystem**. **v2.4 streams each file with `cat > '<remote>'` over a plain exec channel** instead, and was **proven out-of-the-box 2026-11-18**: a 2nd bare GL-MT6000 provisioned entirely from local files → live Z20 map, LOOKOUT + `9076801` units, audio On, **no GitHub touched**. (Firmware lineage, recorded in DEPLOY.md: proven baseline GL v4.11.0; the release just before it is v4.10 then v4.9, so a carton box typically ships on 4.10.x and the first-boot wizard prompts the update.)

**Proven / shipped:** radio → clean NMEA feed; live units in ArcGIS Earth (NetworkLink KML), any browser (Leaflet slippy map), and phones (NMEA/TCP); the box's own position ("you are here") from a local Garmin over libusb; radio audio in the browser (PCM/WebSocket); multi-map menu off an SSD (`.tpkx` or `.mbtiles`); one-click router setup + live unit-renaming (Lookout Manager); a QR-card maker. Runs on a **GL-MT6000** router, a **GL-MT3000** (the battery/man-pack **Traveler** — serial-NMEA GPS, GPS chain proven 2026-11-21), *or* a **Raspberry Pi**.

**Open / optional:** cold power-pull to re-stamp reboot-survival on a given box (already proven); capture the carton firmware version on the next truly-new box *before* updating; the `docs/IDEAS.md` backlog (reverse audio/talk-back, info kiosk, field-photo shared board). Public storefront/polish on Jim's go.

**Lab work lives in [The Signal Shed](https://github.com/Jim-dc95811/The-Signal-Shed)** (new 2026-11-19) — The Lookout's browser-transport lab (audio/video/docs/live-data/phone-GPS). **Staged there, ready to graduate here:** a tested **`units_kml.py` v1.13** patch that adds optional **HTTPS on :8443** (cert-gated — a no-op, byte-identical to v1.12, when no certs are present; :8080 http unchanged) so a phone can share its OWN GPS back and become a unit (`/share`, `POST /report`, `/ca` serves a private "Lookout Fleet CA"). Proven end to end in the sandbox; bench steps (make certs → swap in the v1.13 build → install the CA on a phone) in the Shed's `experiments/28_phone_gps/`. The same cert then unlocks phone camera/mic for free. Don't re-derive it — read the Shed first.

---

## What it is  *(one breath)*

One box — a GL-MT6000 (fixed) or GL-MT3000 (**Traveler**) travel router (OpenWrt), or a Raspberry Pi — reads a telemetry radio's received GPS over USB (RNDIS), a local GPS (**Garmin** over libusb, or a plain **serial-NMEA** puck like the Traveler's VK172), and the radio's **audio** off a USB sound card, and re-serves all of it to every device with **nothing installed on the viewer.** Three small, **isolated**, stdlib-Python services live at `/root`:

- **`bk_bridge.py`** → clean NMEA position feed on **:10110** (TCP), folding in the box's own Garmin fix as the "you are here" unit.
- **`units_kml.py`** → the map server on **:8080**: a NetworkLink `units.kml` for ArcGIS Earth, *and* a browser **Leaflet** slippy map (`map.html` + `leaflet.js`/`leaflet.css`) over offline tiles read straight from `.tpkx`/`.mbtiles` on the SSD, plus the live units and a token-guarded rename endpoint.
- **`lookout_audio.py`** → raw-PCM radio audio over a **WebSocket on :8081**, played in-browser by the Web Audio API (no codec).

Boot = three **procd** init scripts under `/etc/init.d/` (sources in `openwrt/`) + a usb0 hotplug handler + `sync`. Maps live on a USB-hub **SSD**, never the router. The box's position source auto-detects: Garmin-libusb → gpsd → serial NMEA.

---

## THE LANDMINES — read before you touch the thing they name
*Each of these cost a real debugging cycle once. Don't pay again.*

- **Provisioning MUST fetch the browser-map front-end.** `units_kml.py` serves `map.html` + `leaflet.js` + `leaflet.css` from `/root`, and the audio **Listen** button lives *inside* `map.html`. Lookout Manager **v2.1 forgot to fetch them** → the browser map was dead while the "3 services running" check still printed **DONE**. Fixed in **v2.2** (SETUP_STEPS line "Downloading the map page"). **General rule this proves: the setup verify is process-liveness, NOT functional — always do the functional pass (open `:8080`; the map must actually draw).**
- **Firmware first.** `kmod-usb-audio` is **kernel-matched** (5.4.238 on the proven build); a carton box can ship older firmware/kernel and break the match. Update GL firmware *before* provisioning (GL's first-boot wizard prompts it). Proven baseline: **GL v4.11.0 / OpenWrt 21.02-SNAPSHOT / kernel 5.4.238.** → `DEPLOY.md`, `docs/DEVELOPERS_GUIDE.md` §1B.
- **SSH host-key changes on flash/reset.** A firmware update or factory reset regenerates the box's SSH identity at `192.168.8.1`; a *manual* `ssh` then errors "REMOTE HOST IDENTIFICATION HAS CHANGED." Harmless. `ssh-keygen -R 192.168.8.1`, reconnect, accept. The one-click (paramiko auto-accept) never hits it. → `DEPLOY.md` troubleshooting.
- **End every deploy with `sync`.** On this GL/OpenWrt box, overlay writes sit in page cache; a hard power-pull reverts to the last on-flash state and silently loses everything since. `enable` "succeeding" in the shell is not enough. (Lookout Manager does this automatically; a by-hand deploy must not forget it.)
- **`raw.githubusercontent.com` CDN cache** ignores `?v=` cache-busting (~5 min). When you need certainty the box pulled exact bytes, fetch by **commit SHA** (immutable URL) and `grep '^VERSION'` the file before restarting the service.
- **Nested-ssh `wget`: name each file explicitly**, no shell variable — `$f` gets eaten across the Windows-cmd → ssh → OpenWrt-sh layers, arrives literal, and 404s every fetch while looking exactly like a failed push.
- **You cannot test ArcGIS Earth here.** You *can* test the Python logic and the exact KML/tile bytes (do). You **cannot** test how ArcGIS Earth renders or caches KML — its style caching has bitten twice. Anything about AE's *visual* behavior needs Jim's eyes / a screenshot, never a guess.
- **Garmin speaks binary D800 over libusb, not NMEA.** gpsd on this OpenWrt build detects but can't read it; gpsbabel/pyusb aren't packaged. `garmin_linux.py` talks it in pure ctypes/libusb, **discovering the USB endpoints from the device's own config descriptor** (hardcoding them fails `rc=-1`). Only dependency: `libusb-1.0-0`. → `docs/GPS_SOURCE.md`, `docs/GARMIN_ON_OPENWRT.md`, family `CLAUDE.md` §3c (full protocol).
- **Audio driver comes from GL's OWN signed, kernel-matched feed** (`opkg install kmod-usb-audio alsa-utils`) — a generic OpenWrt kmod vermagic-mismatches. Capture handle `plughw:0,0`, S16_LE / 16 kHz / mono. The streamer is a **separate process on its own port** — audio up/down/card-absent must never touch the map or feed. Keep that wall. → `docs/AUDIO_BENCH.md`.
- **No default map (units ≥ v1.12).** The box carries **no** map and not even the *concept* of a default. `units_kml.py` scans the mounted SSD (`/tmp/mountd/*`) and serves every `.tpkx`/`.mbtiles` at `/m/<slug>/`, alphabetical; bare `/` shows the first. **Units never move the view** (IDs key up from all over).
- **Isolation is a design rule, not an accident.** The three services share no state; the same wall keeps the Garmin self-GPS and the audio apart from the position feed. Don't couple them to "simplify."
- **The router's SSH is dropbear — NO SFTP subsystem.** paramiko `open_sftp()` → `EOF during negotiation` (this crashed Manager v2.3's local-files mode on a real box; it passed the sandbox because the stub faked SFTP). To push a file to the box over SSH, stream it with `cat > '<remote>'` on a plain exec channel (write bytes to stdin, `shutdown_write()`), as Manager v2.4's `_put_file` does — never SFTP/scp-subsystem. Ordinary `exec_command` (opkg, enable, start) works fine; only the SFTP channel is missing.

---

## Working with Jim on the box  *(so it goes smoothly)*

- His SSH terminal has **no working paste** — `wget` scripts straight from the repo, keep commands short and typeable, name files explicitly.
- Live hands-on: **one step at a time, wait for his confirmation**; spell out the full exact command every time (he doesn't keep them in memory); ask for a **screenshot**, don't ask him to transcribe.
- Files for him go **straight to his Downloads via the bridge** (`device_commit_files`) — tell him after. A bridge-placed file has no mark-of-the-web (dodges Defender's reputation flag). Commit each change from a **fresh** `/mnt/user-data/outputs/<unique>/` path (the bridge re-sends the first snapshot on a repeated `stagedPath`) and verify size/mtime with `device_list_dir`.
- **Bump the version on every change** — the window-title version is his tell for what's running.
- **Verify, don't assume.** Re-read the actual source before trusting a summary of it — that habit is exactly what caught the v2.1 map.html gap. "Confirm X" means check it with a tool, not from memory.

---

## Where the deep detail lives

| Doc | What's in it |
|---|---|
| `README.md` | Front page — what it is, downloads (Lookout Manager, QR Maker), the hardware diagram. |
| `DEPLOY.md` | The ~5-minute crew quickstart (first-boot → firmware → one-click) + troubleshooting. |
| `docs/DEVELOPERS_GUIDE.md` | Deep reference: hardware, full on-router file layout, shell test/diagnostic commands, measured footprint. |
| `docs/BROWSER_MAP.md` | The in-browser Leaflet map over offline `.tpkx`/`.mbtiles`; the phone-https gotcha; other-hardware tiers. |
| `docs/AUDIO_BENCH.md` | The whole radio-audio build — driver feed, ALSA capture, the PCM/WS streamer, the browser side. **Read before touching audio.** |
| `docs/GPS_SOURCE.md` · `docs/GARMIN_ON_OPENWRT.md` | Self-GPS: auto-detect, the Garmin-over-libusb reader, the gpsd gotcha. |
| `docs/SECURITY.md` (+ PDF) | Security analysis for IT/leadership — pull-not-push, no outbound, the measured ports receipt. |
| `docs/The_Lookout_Beyond_Factory.pdf` (source `docs/graphics/beyond_factory.html`) | The OpenWrt/GL-engineer write-up: stock box → everything added → the measured result, beginning to end. |
| `docs/IDEAS.md` | Backlog (reverse audio/talk-back, info kiosk, field-photo shared board). |
| `docs/TRAVELER.md` | **The Lookout Traveler** — the man-packable, battery MT3000 build: platform decision (MT3000 not Pi), hardware, power design, the two configs (standard + battery-saving, with diagrams), software deltas, what we learned. **Design on record, not built/proven, not public.** The canonical Traveler home. |
| `docs/BK_GPS_DELIVERY.md` | How BK delivers GPS — the two domains (over-air vs gateway), the three gateway paths, where the Lookout taps in; the Bluetooth/LocateONE path is sealed (don't re-chase). |
| **[The-Signal-Shed](https://github.com/Jim-dc95811/The-Signal-Shed)** repo (its `docs/SYSTEMS_DIARY.md`) | The Lookout's **lab** — where new browser transport paths (audio/video/docs/live-data/phone-GPS/camera) are explored and proven before they graduate back here. The box-as-content-platform work lives there to keep this OG pristine. Read its diary before building any new browser-served content. |
| `docs/EASY_INSTALL_PLAN.md` | Handoff for making setup humane for non-Pi users. |
| `lookout_manager/System Files/lookout_manager.py` | The one-click setup + rename app. `SETUP_STEPS` is the provisioning sequence — **every fetch target it names must exist on `main`.** |
| **family `CLAUDE.md`** (ArcGIS-Earth-Unlocked repo) | Highest-authority newest state, owner working-rules, and the full Garmin protocol write-up (§3c). Read for cross-family context. |

---

## Resume procedure

1. Clone `The-Lookout`; attach with push access (`add_repo`, `access: push`) before pushing.
2. Read this file → the one deep doc your task touches (table above) → the live source.
3. Before changing anything the box fetches, confirm the target exists on `main`: `gh api repos/Jim-dc95811/The-Lookout/git/trees/main?recursive=1`.
4. Proven baseline: GL **v4.11.0** / kernel **5.4.238**. Test the Python + exact bytes here; hand AE-visual and hardware checks to Jim.
5. Finish a deploy with `sync`; finish a change with a version bump.

*Keep this file current and lean. Depth belongs in the docs above; this is the map to them, and the list of holes not to fall in twice.*
