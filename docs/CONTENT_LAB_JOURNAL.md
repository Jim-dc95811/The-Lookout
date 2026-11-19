# The Lookout — Content Lab Journal

**Written by Claude, for Claude — a living findings log, updated in real time as we build.**
Jim gets limited time per week with me, so this doc is how that time *compounds*:
every browser data-path experiment gets recorded here the moment it's proven, so a
future session (even a different model) resumes cold without re-deriving anything.
Keep it current and lean; the dated log at the bottom holds the running history.

> Public-safe: strip any employer/agency name (Jim's own name/handle are fine).
> Precedence: live code > the family `CLAUDE.md` (ArcGIS-Earth-Unlocked) > The Lookout's
> `CLAUDE.md` > this journal. This journal owns the **content-lab / data-path** thread.

---

## The thesis (why this exists)

The Lookout started as a map server. The real discovery is bigger: **the box is a
content & data distribution platform.** It sits on its own Wi-Fi with no internet, and
any device with a browser can reach it. So the question stops being "can it serve a
map" and becomes **"what can a plain browser eat and emit — and the box be the source
and sink of — with nothing installed on the viewer?"**

Jim's framing, kept verbatim because it's the north star:
- **The range** — anything a phone can *receive* over Wi-Fi, the box can be the source of.
- **The mirror** — anything a phone can *send* over Wi-Fi, the box can take back.
- And the quiet punchline: a button on a screen that *does something* — where the thing
  it talks to is **in the truck**, not a server in San Jose.

Everything here is a concrete answer to that question, each one built self-contained,
offline, and **tested by me before Jim sees it.**

---

## The tier model (the finding that governs everything)

Every data path falls into one of three honest tiers. Say which, always — it's the
difference between a promise that holds in the field and one that embarrasses you.

| Tier | What it unlocks | Cost |
|---|---|---|
| **browser · today** | files in/out, audio, video, slides, zoomable imagery, live canvas/data, forms, photo *upload* (`<input type=file capture>`) | plain http, nothing installed |
| **+1 cert on the fleet** | live **camera / mic / GPS** (`getUserMedia`, Geolocation), service workers / PWA install | one locally-trusted cert pushed to the devices — still just a browser |
| **+ an app** | raw sockets, Bluetooth, background operation | Android sideloads an APK from the box; **iOS blocks local sideload** (App Store / MDM only) |

Why the cert line exists: browsers gate camera/mic/GPS and service workers behind a
**secure context** (https). A plain-http offline box can't give them that without a
cert trusted on each device. File-upload camera-capture is the exception — it works on
plain http today — which is why the "mirror" works now and *live* camera doesn't.

---

## Proven paths

All three delivered to Jim's Downloads (not the repo — they're explorations). Each was
render-verified **and** function-verified headless before hand-off.

| Path | File | What it proves | Honest note |
|---|---|---|---|
| **Content Lab** | `Lookout_Content_Lab.html` | 9 data paths in one offline page: audio, video, HTML slide deck, photo gallery+lightbox, pan/zoom image, live-ticking data tile w/ sparkline, form+photo-upload "mirror", rich-doc, file download | One page, ~464 KB with all media embedded as data URIs. The tier legend is baked in so it answers "can it do X" honestly. |
| **Service Manual** | `Lookout Service Manual/` (folder) | A PDF-killer: the Developer's Guide reflowed + **search-as-you-type** (highlight, prev/next, count), a **vector** system diagram (sharp at any zoom, theme-aware), a **raster** wiring plate in a pan/zoom viewer, scrollspy TOC, phone drawer | **268 KB vs the 232 KB+ PDF — but searchable, reflowing, zoomable.** Ships as a *folder* so its relative links to companion PDFs resolve (see landmine below). |
| **Audio Scope** | `Lookout_Audio_Scope.html` | **audio → live visual.** Web Audio `AnalyserNode` drives a waveform, a spectrum (peak-Hz readout), and a transmission-level meter on the box's own 3%/54% scale | Candidate **real feature**: rides under the map's 🔊 Listen button, fed by the live radio PCM (`:8081`) — a crew *sees* a transmission land with the volume down. Proven reactive, not canned (see test method). |

---

## Landmines (each cost a real cycle once — don't pay again)

- **A lone HTML is only self-contained if it *embeds* everything.** The moment it
  *links* to a sibling file (a companion PDF, an image), it must travel as a **folder**,
  or the relative link 404s when opened from Downloads. Embed assets as data URIs when
  you can; bundle a folder when you can't. (Caught live: the Service Manual's
  "hardware requirements sheet" link broke until shipped as a folder with `graphics/`.)
- **Search must skip SVG.** A text-highlight TreeWalker that wraps matches in `<mark>`
  will silently *delete* the matched text inside an inline `<svg>` — SVG ignores the
  `<mark>` element. Exclude `p.closest('svg')` from the walk. (Searching "audio" turned
  "lookout_audio.py" into "lookout_.py" in the diagram until fixed.)
- **Secure-context gate.** Camera/mic/GPS/service-workers need https. Don't promise live
  camera on the plain-http box; promise photo *upload* (works) and note the cert path.
- **Media that plays everywhere:** MP3/M4A(AAC) audio and **H.264** MP4 video play on
  iPhone + Android + desktop. Avoid OGG/Opus (trips older iOS).
- **Tiles are flat-cost.** The box seeks one 256 px tile per request off the SSD, no
  decode — map/library size doesn't scale RAM/CPU. "Infinite in puny human terms — just
  buy a bigger SSD" (Jim). The same tiling handles a monster diagram or a 2,000-page
  manual's plates.

---

## My build & test method (so a future me matches the bar)

1. Build the page self-contained (assets as data URIs; folder only when it links out).
2. **Render-verify** with Playwright at desktop *and* ~390 px phone — no horizontal
   scroll, reflows to one column.
3. **Function-verify**, not just render: drive the real behavior headless and assert the
   mechanism. (Audio Scope: played the sweep clip, sampled the live spectrum twice,
   asserted the peak bin *climbs* 17→31 and level>0 — proof it tracks the audio, not a
   fake animation.) Launch Chromium with `--autoplay-policy=no-user-gesture-required`
   for audio tests; expose `window.__hooks()` to read internal state.
4. Deliver to Jim's Downloads via the bridge from a **fresh** `/mnt/user-data/outputs/<uniq>/`
   path, **distinct filename** each time.

---

## Paths to try next (the backlog)

- **"Drop a doc on the box" builder** — point it at a folder of markdown/PDF → emits a
  Service-Manual-style bundle, links wired. Turns the one-off into a repeatable tool.
- **Fold the Audio Scope into the real Listen button** (map.html, fed by `:8081`).
- **Field incident board** — the "mirror" made shared: phones post text+photo, all
  appear on one page every device sees. Needs a tiny POST sink on the box (server side).
- **Slide deck from a real `.pptx`** (export → images/HTML, flip in browser).
- **Live dashboard from a real sensor/SCADA side-pipe** (the `:10110` feed is the model).
- **2,000-page service manual, tiled** — words reflow, plates tile like imagery; the box
  as a wireless manual library.
- **QR deep-links** to a specific page/map (Lookout QR Maker already does map links).

---

## Session log

- **2026-11-19 (Thu):** Started this journal at Jim's request ("document these findings
  in real time"). Built and proved three browser data-path combos in one evening:
  **Content Lab** (9 paths, one page), the **Service Manual** (reflow+search+vector/raster
  diagrams; learned the folder-bundle rule the hard way when its companion-PDF link 404'd
  from Downloads, fixed by shipping a folder), and the **Audio Scope** (audio→live
  waveform/spectrum/level; function-tested the reactivity — sweep peak bin climbed 17→31).
  Established the tier model and the SVG-search landmine. Jim: "It's the new revolution,
  build it and they will come." Direction set: the box is a content/data platform, and
  this journal tracks every path.
