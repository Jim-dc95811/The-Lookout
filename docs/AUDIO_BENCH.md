# The Lookout — radio audio over the browser (bench record)

**Status: BENCH-PROVEN LIVE on 2026-11-17, not released.** Lives on branch
`audio-bench` only — NOT on `main`, NOT in the montage/all-tools/storefront.
Nothing public until the capacity test + boot-service wrap are done and Jim says go.

This is the complete engineering record of adding **live radio audio** to the
Lookout's in-browser map: a crew member opens `http://<router>:8080/`, taps a
**🔊 Listen** button, and hears the radio net while watching the units move —
no app, no install, on a phone or a locked-down PC.

---

## 1. What it is, in one paragraph

A USB sound card on the router takes the radio's received audio. The router
captures it with ALSA (`arecord`) and a tiny Python process (`lookout_audio.py`)
streams it as **raw PCM over a WebSocket** to any browser. The map page
(`map.html`) grows a Listen button that plays that PCM with the **Web Audio API**.
No codec anywhere — voice is narrowband, so it ships **16 kHz / 16‑bit / mono**
(~256 kbps), which is nothing on a LAN and costs the router almost no CPU (it's a
byte copy, not an encode). The streamer is its **own isolated process on its own
port (:8081)**; it shares no state with `bk_bridge.py` or `units_kml.py`, so audio
being up, down, or the card unplugged has zero effect on the map and position feed.

This is "Door 1" in spirit — a code-free *consume* path for the no-install client
classes (Group-Policy PC, smartphone): see the objective in CLAUDE.md.

---

## 2. Hardware

- **Sound card:** Creative **Sound Blaster Play! 3** (USB Audio Class).
  Enumerates as `card 0: S3 [Sound Blaster Play! 3], device 0: USB Audio`.
  Comes up **full-speed (USB 1.1, 12 Mbps)** — plenty for voice (even CD-quality
  stereo is ~1.5 Mbps). Plugged into the **powered USB hub** alongside the radio
  (RNDIS), the SSD, and the Garmin GPS.
- **Radio audio patch:** the radio's audio-out goes into the card's **input jack**
  (the pink/mic jack on the Play! 3, *not* the green output). Measured levels were
  healthy (see §5) feeding the mic input directly; no pad was needed on this radio.
  If a future radio runs hotter and the meter pins at 100%, pad it down (resistive
  divider) or use a line-in card.

## 3. Router / OS facts (so you don't re-discover them)

- Box: **GL-MT6000** (MediaTek MT7986, quad A53, 1 GB RAM), OpenWrt
  **21.02-SNAPSHOT r15812**, **kernel 5.4.238**, GL firmware feed **4.5.7**.
- The base GL build is **lean**: no `/dev/snd`, no sound kernel modules loaded.
- **The make-or-break was whether the USB-audio driver is installable from GL's
  own signed feed without a firmware rebuild — it is.** `opkg update` pulls a
  **kernel-matched kmod feed** at
  `https://fw.gl-inet.com/releases/mt798x/kmod-4.5.7/aarch64_cortex-a53/mediatek/mt7986/`.
  Because it's built for this exact kernel (5.4.238), the module's vermagic matches
  and opkg installs it cleanly. (A generic OpenWrt kmod would mismatch and be
  refused — always use GL's own feed on GL firmware.)

## 4. Install (one time, writes a few hundred KB to overlay flash, reversible)

```
opkg update
opkg install kmod-usb-audio alsa-utils
```

That pulls, all from GL's signed feed:
- **`kmod-usb-audio` (5.4.238-1)** — the USB-audio driver (the make-or-break).
- **`kmod-sound-core` (5.4.238-1)** + `kmod-input-core` — dependencies.
- **`alsa-utils` (1.2.4-1)** + `alsa-lib` + `alsa-ucm-conf` — gives us `arecord`.

After install the driver binds to the already-plugged card and `/dev/snd` appears.
(If the card was plugged in *before* the driver and doesn't bind: unplug/replug.)

Also available in the feed if ever wanted (NOT used — the lean plan needs none):
`sox` (record+resample), `libopus`/`libopusenc`, `ffmpeg`, `icecast`.

**Remove the whole thing:** `opkg remove kmod-usb-audio alsa-utils` (+ the deps if
you want them gone). Fully reversible.

## 5. Capture — the device, the format, the levels

- Confirm the capture device: `arecord -l` →
  `card 0: S3 [Sound Blaster Play! 3], device 0: USB Audio … Subdevices: 1/1`.
- Capture handle: **`plughw:0,0`** (the `plug` layer auto-converts rate/format, so
  requesting 16 kHz mono works regardless of the card's native rate).
- Format: **S16_LE, 1 channel, 16000 Hz.**
- Live level check (no file, just a VU bar):
  ```
  arecord -D plughw:0,0 -f S16_LE -c 1 -r 16000 -V mono /dev/null
  ```
  **Measured 2026-11-17: idle ≈ 3%, a transmission ≈ 54%.** That's the sweet spot —
  clean, real headroom, no clipping. (30–80% on signal = good; pinned 100% = too
  hot, pad it; stays at idle during a transmission = signal isn't reaching the jack.)

## 6. The streamer — `lookout_audio.py`

Pure Python **standard library only** (no PyPI, no codec). Its own process, own
port. Run:

```
python3 /root/lookout_audio.py          # live: capture from the card
python3 /root/lookout_audio.py --test   # no card: emit a 440 Hz test tone
```

Prints `[audio] WebSocket PCM server on 0.0.0.0:8081 (16000 Hz, 16-bit, mono)` and
`[audio] listener on <ip> - N now` as browsers connect.

Design points (all deliberate):
- **Isolation:** never imports or touches `bk_bridge`/`units_kml`; no shared files,
  locks or threads. If it dies or the card is gone, the map/position feed are
  unaffected. Same wall we put around the Garmin self-GPS.
- **Source:** spawns `arecord -D plughw:0,0 -f S16_LE -c 1 -r 16000 -t raw -q` and
  reads its stdout in **3200-byte chunks (~100 ms)**. Auto-restarts arecord if it
  ever ends (card yanked) — never crashes the server.
- **WebSocket (hand-rolled, ~60 lines):** does the `Sec-WebSocket-Accept` handshake
  (SHA1 of key + the WS GUID, base64), then sends **binary frames (opcode 0x2),
  server→client unmasked**, with correct 7/16/64-bit length framing.
- **Lock-free fan-out:** copies the client list under a lock, then sends *outside*
  the lock, so one slow listener can't stall the others. Each client socket has a
  **2 s send timeout**; a stuck listener is dropped, never freezes the feed. (This
  is the same "stuck-client" lesson from the units_kml hardening.)
- **Env overrides:** `LOOKOUT_AUDIO_PORT` (8081), `LOOKOUT_AUDIO_RATE` (16000),
  `LOOKOUT_AUDIO_DEV` (plughw:0,0).

## 7. The browser — Listen button in `map.html`

Added a `🔊 Listen` button (`#listen`) in the top status bar, and a small
self-contained IIFE at the end of the page script:

- On click: create/resume an **`AudioContext`** inside the click handler (satisfies
  the browser **autoplay** policy — audio only starts on a user gesture), open a
  `WebSocket` to **`ws://<same host>:8081`**, `binaryType="arraybuffer"`.
- Per message: `Int16Array` → `Float32` (`/32768`) → `ctx.createBuffer(1, n, 16000)`
  + `copyToChannel` → an `AudioBufferSourceNode` scheduled **gaplessly** against a
  running `nextTime` cursor with a **~150 ms jitter buffer** (re-primes on underrun
  so a late packet causes a brief gap, not a lasting glitch). The context resamples
  the 16 kHz buffer to its native rate automatically.
- **Graceful degrade:** if the streamer isn't running, the WS never opens and the
  button shows **"no audio"** — the map is completely unaffected. Button goes green
  (`#listen.on`) and reads "🔊 On" while playing.

**Reconnect + wake-lock (added 2026-11-17 pm, after a live bench drop).** The box
drops any listener that goes quiet for 2 s (`SEND_TMO`, §6) so one stuck screen can't
stall the fan-out. On the bench a phone that dimmed hit exactly that: the box printed
`[audio] listener gone` and the browser — which closed the socket and gave up — flipped
the button back to "Listen" after ~2 s. Fix (map.html only, streamer untouched):
- The page now separates **intent** (`on`, set by the user's tap) from the **socket**.
  A drop while `on` is true **auto-reconnects** (1 s backoff) and holds the button "On"
  (shows "🔊 …" during the gap); a hiccup becomes a short gap, not a dead button.
- Only a socket that **never opened** (streamer down) falls back to "no audio"
  (`everOpen` flag) — so the old graceful-degrade still works, but a *dropped* live
  session no longer gives up. Restarting the streamer makes audio return on its own.
- A **screen wake-lock** (`navigator.wakeLock`) is held while listening, so a phone
  stops dimming in the first place (the root cause of the drop). Wrapped in try/catch;
  degrades silently where unsupported. Re-acquired on `visibilitychange` (the lock is
  auto-released when a tab hides), alongside an `AudioContext` resume and a socket
  re-check, so returning to a backgrounded tab re-arms cleanly.
- Verified headless (Playwright): a stand-in streamer that drops connection #1 mid-play
  → the page reconnects as connection #2 and keeps playing, button stays "🔊 On", 0 JS
  errors. The everyday case is covered; the **worst-case capacity test** (a truly stuck
  listener gapping everyone up to 2 s via the sequential sender) is still the open item.

## 8. Networking

- Audio WS is on **:8081**; the map is served by `units_kml.py` on **:8080**. The
  page (from :8080) opens a cross-origin WS to :8081 — browsers allow that; no CORS
  needed for WebSockets.
- **Firewall:** on this GL build the LAN zone input is ACCEPT, so **:8081 was
  reachable on the LAN with no extra rule** (same as :8080). If a future build
  blocks it, add a LAN-zone traffic rule allowing TCP 8081.
- **Phone gotcha (unchanged):** type `http://<router>:8080/` — phones force https.

## 9. Deploy to a box (bench procedure used 2026-11-17)

1. `opkg update && opkg install kmod-usb-audio alsa-utils`  (§4)
2. Patch the radio audio into the card's input jack; confirm with §5.
3. Get the two files onto the box next to `units_kml.py` (i.e. `/root`):
   - `lookout_audio.py` → `/root/lookout_audio.py`
   - the audio-enabled `map.html` → `/root/map.html` (**back up the old one first:**
     `cp /root/map.html /root/map.html.bak`).
   - Delivery used this session: `wget -O <path> <branch raw URL>` (first fetch of
     brand-new files, so no CDN-cache issue). For a **re-fetch after an edit**, use
     the **commit-SHA** URL (raw.githubusercontent caches branch URLs ~5 min and
     ignores `?v=`), and always name each file explicitly in the wget (the `$f`
     gremlin). The desktop bridge (scp from Downloads) was offline this session.
4. `python3 /root/lookout_audio.py` (foreground to watch logs).
5. Open the map, **hard-refresh (Ctrl+F5)** to pull the new page, tap **🔊 Listen**.

**Undo:** `cp /root/map.html.bak /root/map.html` restores the original page
instantly (units_kml serves it live, no restart); stop the streamer with Ctrl+C.

## 10. Proofs

- **WS framing (sandbox):** a stdlib WebSocket client got a valid `101` + correct
  accept key, then 6 binary frames of 3200 B each, opcode 0x2, unmasked, peak PCM
  amplitude 8000 (the test tone) — real audio, not silence. PASS.
- **Browser end-to-end (headless Chromium / Playwright):** Listen button present,
  click → "🔊 On" (WS connected to the streamer), **19 PCM buffers decoded
  in-browser in 1.8 s**, **zero JS errors**. Proves WS → Int16 → Float32 →
  Web Audio works and the page script is clean. PASS.
- **LIVE (the real thing), 2026-11-17 ~12:26:** radio audio heard on Jim's **PC and
  phone** browsers, map showing "2 units" + the green 🔊 On button, over Z20 aerial
  imagery, **nothing installed on either device**. Capture measured clean (idle 3%,
  transmission 54%). This is the proof Jim required before anything public.

The only things the sandbox can't prove are *audible* sound (needs a speaker) and
the *real* radio capture — both confirmed live above.

## 11. Capacity & integrity (the honest read)

- **CPU:** PCM passthrough is a memcpy per listener; ~16 KB/s per stream. A few
  listeners ≈ +2–5% CPU, steady. (We deliberately did **not** encode — encoding is
  where the CPU cost and the "80%, no elbow room" risk would come from. Ship PCM.)
- **RAM:** negligible (a few KB ring per listener).
- **LAN:** ~128–256 kbps per listener; trivial.
- **The real risks (neither is the capacity meter):**
  1. **USB bus contention** — audio is isochronous; the SSD does bulk bursts during
     a hard map pan. On a cheap UAC dongle + shared hub this can cause **audio
     glitches under heavy panning** (a quality dropout, not a crash). Mitigate with
     a decent dongle and, if possible, the SSD on a different USB port from the card.
  2. **A new real-time obligation** — the box's first always-on, latency-sensitive
     job. Mitigated by the strict **process isolation** above: an audio failure is a
     shrug, not an outage.
- The capacity number is not what threatens integrity — the isolation is what
  protects it. Keep audio walled off from the core.

## 12. OPEN — what's left before this is ever public

1. **Worst-case capacity test (the integrity gate):** several listeners **+** a hard
   Z20 pan **+** a live transmission, all at once, watching `cat /proc/loadavg`,
   free RAM, and `dmesg` for ALSA xruns. This tells us the true headroom, not my
   estimate.
2. **Boot-service wrap — BUILT 2026-11-17** (`openwrt/lookout-audio`, `START=97`,
   `respawn`, same shape as `bk-bridge`/`units-kml`), after the hand-run streamer was
   found to die with its SSH window (no box can keep a PC attached). Install on the box:
   ```
   wget -O /etc/init.d/lookout-audio https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/<audio-bench-SHA>/openwrt/lookout-audio
   chmod +x /etc/init.d/lookout-audio
   /etc/init.d/lookout-audio enable
   /etc/init.d/lookout-audio start
   ```
   Confirm: `pgrep -f lookout_audio` prints a PID; `logread -e lookout_audio` or
   `logread | grep audio` shows the `[audio] WebSocket PCM server on 0.0.0.0:8081` line
   (procd routes stdout/stderr to the system log, not a terminal). Disable/undo:
   `/etc/init.d/lookout-audio disable; /etc/init.d/lookout-audio stop`. Reboot-survival
   still to be proven with a cold power-pull (like the other two services were).
3. **Merge `audio-bench` → `main` + Lookout Manager one-click (install the two
   packages + fetch the files) + README/montage** — only after 1 & 2 and Jim's go.
4. Nice-to-haves: input pad option for hot radios; a tiny level indicator; a mute
   persistence per viewer (localStorage); squelched vs. open-audio choice is a
   radio-side decision, not ours.

## 13. From-scratch quickstart (for a fresh box)

```
# 1. driver + recorder (GL feed, no firmware rebuild)
opkg update && opkg install kmod-usb-audio alsa-utils
# 2. plug the sound card into the hub, radio audio -> card input jack
arecord -l                                   # expect card 0: Sound Blaster...
arecord -D plughw:0,0 -f S16_LE -c 1 -r 16000 -V mono /dev/null   # Ctrl+C; expect the bar to move on a transmission
# 3. files next to units_kml.py (/root), back up map.html first
cp /root/map.html /root/map.html.bak
#   put lookout_audio.py and the audio-enabled map.html in /root
# 4. run it
python3 /root/lookout_audio.py
# 5. open http://<router>:8080/ , hard-refresh, tap 🔊 Listen
```

---

*Branch `audio-bench` (first build commit `c3438c8`). Employer-clean — keep it that
way. When proven and merged, fold this into the main docs and retire the branch.*
