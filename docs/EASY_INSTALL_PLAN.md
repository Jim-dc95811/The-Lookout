# The Lookout — easy-install plan (a handoff to the next Claude)

Hey — you're picking up the biggest piece of The Lookout: making it possible for a **non-Pi person** to stand one up. Jim asked me to write this as a friend to you, so you don't have to re-derive everything I already worked out with him. Read it before you touch anything. It carries the honest framing we agreed on, what's already proven, the build order, the research to actually do, the traps, and how Jim works. The live state of the whole family is in the umbrella [`CLAUDE.md`](https://github.com/Jim-dc95811/ArcGIS-Earth-Unlocked/blob/main/CLAUDE.md); this doc is the deep dive for just this task.

---

## 0. The north star — and the honesty rule that governs it

The goal: **stand up a Lookout with as little skill as is *truthfully* possible.**

The word that matters is *truthfully*. Jim's explicit value, in his words: *"I want to be honest with them."* He would rather tell a user "this part is beyond you, get help" than ship a polished lie that strands them. **Do not oversell "1-click."** If you write a plan or a doc that pretends a novice can do the hard parts, Jim will catch it and it costs trust. Honesty > polish, every time.

We already had the hard conversation and reached these conclusions — treat them as settled unless Jim reopens them:

1. **A Raspberry Pi is not an "average Joe" device to set up, and no GUI changes that.** The hard part isn't clicking — it's that a Pi is **headless and fails silently**. When it doesn't come up (wrong SD card, weak PSU, no network address, radio not seen), there's no screen and no error, just a blinking light. A novice can't tell *which* thing failed. That floor is a Pi/headless reality, not a Lookout bug.
2. **You can't lower that floor — you can only *move* it.** Put all the hard skill on **one capable person** (Jim, or one tech per district) who images and configures a finished box. The novice then just **powers an appliance** — like a radio: crews don't program the radio, the tech does. The finished-box path is the only truly novice-friendly one, and it's a good one. Design the product around it.
3. **The Pi is the price of dodging Group Policy.** The whole reason we're on a Pi is that the work PCs are locked down (no Python/admin). An unmanaged $35 Linux box sidesteps that. Its setup friction is the *cost* of the dodge. Name that cost out loud in the docs; don't hide it.
4. **The "hand it to your own Claude" handoff is a real strategy, not a cop-out** — for the DIY middle tier. Make the easy steps dead-simple, then let an AI walk *that* user through *their* network and *their* silent failure in real time. But an AI can only help if the Pi can **report its own status** — otherwise the helper is staring at the same blinking light.

### The honest skill tiers (keep this table truthful in every doc you write)

| What they do | Who can really do it |
|---|---|
| Power a finished, pre-configured box — plug in 3 cables, turn it on | **Near-anyone.** The only truly novice path. |
| Flash a ready-made image themselves (Imager → pick the *right* SD card → write) | **Motivated beginner + a good guide** — real risk of wiping the wrong drive. |
| Get it on a network, reachable, and recover when it's silent | **Intermediate / a tech.** Where average Joe falls off, full stop. |
| Adapt to a different radio / change config | **A tech.** |

---

## 1. What already exists and is PROVEN (don't rediscover this)

The Lookout is two small Python workers, both proven live on Jim's bench on 2026-11-14:

- **`bk_bridge.py`** — connects to the GPS-telemetry radio over its USB-RNDIS link, subscribes, pulls the clean NMEA out, and fans it out on **TCP `:10110`** to any number of clients. Runs as a boot service (`bk-bridge.service`). Proven: connect → subscribe → serve, stable heartbeats.
- **`units_kml.py`** — reads the *bridge's* feed (never a 2nd radio connection), pairs each `$GNGGA` position with its `$PP25` unit ID (reusing the P25 tracker's `StreamParser` **verbatim**), tracks latest-fix-per-unit, and serves a live **`units.kml`** on **HTTP `:8080`**. Has a `--demo` mode (moving synthetic units, no radio). Proven: pipeline verified in a sandbox, then **3 named units served from the Pi moved live in ArcGIS Earth with nothing installed on the PC** (proof shot: `images/live_units_arcgis_earth.jpg`).
- **`Live_Units.kml`** — a NetworkLink the viewer opens once; ArcGIS Earth 3.0.1 re-pulls it every few seconds on its own (`onInterval` refresh — **proven live**). This is the whole no-Python consume path.
- **Boot services**: `bk-bridge.service`, `units-kml.service`.

**Both workers are done.** The only thing left for the *tracking* itself is a real field unit transmitting (bench has only the base relay). Jim's rule: **no family storefront until that field-proof** ("hold off on the family storefront until we have proven workers").

So this task is **not** about the tracking — it's about **making setup humane.**

---

## 2. The decided architecture for easy install

Four pillars, all agreed with Jim:

1. **Ship it as a finished appliance.** The deliverable is a *configured box* (or an image that becomes one on first boot), not a pile of commands. The capable person does the skilled part once.
2. **Push the install to flash-time.** Instead of SSH-ing in and running commands after boot, everything (Python is already in Pi OS, the two scripts, both services enabled, the usb0 config) is baked into a **ready image** or installed by a **first-boot run-once script**. After flashing: plug in radio → power on → it's a Lookout. No post-boot commands, ever.
3. **Aliases = a web page the Pi serves, not a Windows app.** The Pi already runs an HTTP server (`units_kml.py` on :8080). Add a small admin page there. The user opens `http://<pi>:8080` (ideally `http://lookout.local:8080` via avahi) in *any* browser — phone, tablet, locked PC — sees the units, types names, saves. It writes `aliases.json` on the Pi. No install, cross-platform, on-brand ("the Pi serves everything"). **This is the alias-table GUI Jim asked for.**
4. **Self-diagnostics so nothing fails silently.** A status the Pi reports — radio reachable? usb0 up? bridge running? units flowing? disk/OS ok? — in plain language. This is what turns a blinking-light mystery into something a person (or their AI) can act on. It's also what makes the "hand it to your Claude" path actually work.

---

## 3. Build order — split by what you can prove HERE vs. what needs Jim's Pi

**Respect this boundary and tell Jim about it up front (he values it):** this cloud sandbox **cannot build or boot a real ARM Raspberry Pi image, and cannot test on Pi hardware.** You can write and logic-test the software; the image and the on-hardware behavior are Jim's to flash and confirm. Never claim the image "works" until Jim has booted it.

### Phase 1 — buildable AND provable in the sandbox (start here)

1. **Web admin + alias editor on `units_kml.py`.** Add routes: `GET /` (a clean page: live units list + status + an alias editor), `GET /units.kml` (unchanged), `GET /aliases` (current table as JSON), `POST /aliases` (save `aliases.json`). Keep it dependency-free (stdlib `http.server`), theme it simply, and make it phone-friendly. **Prove it** with the existing sandbox HTTP test pattern (see `test_pipeline.py` approach): POST an alias, GET units.kml, confirm the name shows. This single piece delivers the alias GUI with zero hardware and zero install on any client — do it first.
2. **Self-diagnostics (`/status` + a console `--check`).** Plain-language pass/fail for each dependency. Logic is fully testable here with stubs. Output must read like a human wrote it ("Radio: reachable ✓" / "Radio: can't reach 10.250.46.6 — check the USB cable and that usb0 has an address").
3. **First-boot run-once installer** (`firstboot.sh` + a one-shot `lookout-firstboot.service`): copies the scripts into place, installs + enables both services, sets the usb0 config, then disables itself. Write it, shellcheck-lint it; Jim proves it on hardware. Design it to read config (radio IP/subnet, hostname) from a plain text file on the boot partition so a non-Pi person can edit it in Notepad on Windows before first boot.
4. **The AI-handoff guide** — a plain-language page written *for an AI to read and act on*: the architecture map, the five failure modes and their decision trees, what to ask the user to check, how to read the Pi's self-diagnostics. "Paste this whole page to your AI and it can walk you through it." This is the thing that makes tier-2/3 survivable.
5. **Tiered, honest install docs** — rewrite/extend `docs/SETUP.md` around the three paths (finished box / flash-an-image / DIY-with-AI), each telling the reader truthfully what it demands. Keep the skill-tier table from section 0.

### Phase 2 — needs Jim's Pi (plan it, write the pieces, let him prove)

6. **Bake the ready image.** Decide: `pi-gen` (clean, reproducible, bigger effort) vs. configure a stock Pi OS install once and clone the card to a `.img` (fast, Jim can do on his bench). Likely start with the clone-the-card route for a first distributable image, move to `pi-gen` if it goes wide.
7. **Flash-time customization** via Raspberry Pi Imager's OS-customization (hostname `lookout`, enable SSH as a fallback, WiFi creds, run-once). Document the exact clicks.
8. **Network discovery reality.** Confirm `lookout.local` (avahi) works on typical networks; design a fallback (the Pi could show its IP somehow, or a direct PC↔Pi cable with a fixed IP for the no-network case). The agency-network case may still need IT — be honest about it.
9. **Hardware BOM** — the exact Pi model, PSU, and SD card to recommend so novices don't pick wrong (underpowered PSU and bad SD cards are classic silent-failure causes).

---

## 4. The research to actually do (Jim said "research and figure out" — so do it, search-first)

Per Jim's standing rule, **web-search these rather than answering from memory** — they're product-version-specific and change:

- Raspberry Pi Imager's current **OS customization / run-once** capabilities (hostname, SSH, user, WiFi, first-run script) on the current Imager + Pi OS (Bookworm-era): exact mechanics and file locations (`/boot/firmware/`, `cmdline.txt`, `firstrun.sh`, `custom.toml`).
- **First-boot run-once** on current Pi OS: the cleanest supported hook for a one-shot installer service.
- **`pi-gen`** for a distributable custom image vs. card-clone: effort, size, licensing for redistribution.
- **avahi / `.local`** reliability across typical and locked networks; discovery fallbacks.
- **USB-RNDIS enumeration portability** — we proved the radio comes up as `cdc_ether`/`usb0` on Jim's Pi 4 + current OS; confirm it holds across Pi models/OS versions you'd recommend.
- **Hardware BOM** — current recommended Pi + PSU + SD for a headless appliance.

---

## 5. Traps and boundaries (be a friend — here's what'll bite you)

- **The sandbox can't touch Pi hardware or build an ARM image.** Phase 2 is Jim's to flash/boot. Say so before you start; don't imply otherwise.
- **The irreducible floor is real.** Networking + silent-failure recovery is not novice. Don't write a plan or doc that pretends it is — see section 0.
- **Reuse proven code.** `units_kml.py` already lifts `StreamParser` verbatim from `p25_core.py`. Don't reinvent parsers or re-solve solved problems; search the repo first.
- **The `$PP25` format has a comma before the checksum** (`$PP25,<id>,*cs`), so `split(",")[1]` is a clean ID. A `$PP25` *without* that comma would carry the checksum into the ID. The verbatim parser handles the proven format; don't "fix" it without a reason.
- **Deliver test builds via the bridge to Jim's Downloads** when the session is linked (`device_commit_files` to `C:\Users\dc958\Downloads`). Windows-side downloads have a Defender false-positive history (see the umbrella CLAUDE.md "DEFENDER RULE 2"); the bridge path sidesteps it. For the Pi itself, files go up with `scp`.
- **Keep it public-safe.** This repo is public and MIT. No employer/agency names anywhere (Jim's "zero reference to my employer" rule). Jim's own name is fine. Never commit the Pi password or any credential.

---

## 6. How Jim works (the stuff that saves you pain — full version in umbrella CLAUDE.md §2b)

- Terse approvals: **"go" / "engage" / "publish"** = do it. A screenshot = acceptance; don't press for more.
- Best decision format: **findings ranked by importance, one-line consequence each, then a single recommendation.** He usually takes the recommendation.
- **Plain words.** He's not a coder — he's a 37-year radio/electronics expert with deep systems intuition. Name buttons and files exactly; skip code detail unless asked. Explain the *why* at the systems level and he's right there with you.
- **Ask for a screenshot, don't ask him to transcribe** what's on his screen.
- **One thing at a time** during live hardware work. Tonight the recurring snag was the **wrong-window `scp`/`python3`** mix-up: `scp` runs in the **Windows** Command Prompt (pushes the file up); `python3 <script>` runs in the **Pi** SSH window (green `user@host` prompt). Tell him which window, every time.
- **Verify each step** before relying on it (his standing rule), and **search the internet first** for a known easy solution before hand-rolling (his other standing rule). Both are saved preferences — honor them without being asked.
- **Put deliverable files directly in his Downloads** and tell him after.

---

## 7. Definition of done

- **Finished-box path**: a novice can plug in + power on + edit unit names in a browser. No command line.
- **DIY path**: honest tiered docs + the AI-handoff guide + Pi self-diagnostics, so a motivated non-expert (with an AI) can get there and knows truthfully when they can't.
- **Field-proof** of the tracking with a real transmitting unit still stands as the gate before the family storefront (Jim's rule).

## 8. First move for the next session

Start **Phase 1, item 1: the web admin + alias editor on `units_kml.py`.** It needs zero hardware, it's fully provable here, and it hands Jim the alias-table GUI he asked for — in a browser, on any device, with nothing installed. Build it, prove it with the HTTP test, deliver it to his Downloads, and let him open `http://<his-pi>:8080` to see it. Then move down Phase 1.

Be honest, be a friend to the user the way Jim is, and don't pretend the hard parts are easy. — Claude, 2026-11-14
