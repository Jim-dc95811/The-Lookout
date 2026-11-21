# The Lookout — Journal of Ideas

Captured ideas for later, not built yet. Newest first. An entry here is a
direction to weigh, not a committed plan.

---

## WAN uplink + port-forward — publish the Lookout into an existing network — *2026-11-20*

**The idea (Jim):** the GL box is a full router (WAN + LAN + firewall + port-forward),
so instead of only being an **island you join**, connect its **WAN** to an existing
private network and **port-forward `:8080`** — now everyone already on that network
opens the map at the box's WAN IP, without joining the Lookout's WiFi. The box can do
**both at once**: its own WiFi island for direct clients *and* uplink/forward into the
upstream net. Trivial on GL (port-forward UI, or `uci firewall`).

**Good uses (networks you control/trust):** a command vehicle's own router, an
isolated incident network, a home/bench lab — publish the live map into a net people
are already on.

**Cautions — this flips the security posture (island → exposed):**
- The map server has **no auth** (fine on an island). Forwarding it exposes it — **and
  the NMEA feed `:10110` and the token-guarded rename endpoint** — to that *whole*
  upstream network. Only do it on a network you control and trust. The SECURITY.md
  "isolated, nothing leaves, three ports" story assumes the island model.
- **Agency network = explicit IT approval first.** An unmanaged self-built router
  forwarding ports on their LAN is exactly the pattern security teams hunt for.
- **Never forward the *Lookout's* services to an internet-facing WAN** (cellular
  uplink, or upstream of a public net) — the map (`:8080`), feed (`:10110`) and rename
  endpoint have **no auth**, so exposing them to the internet is a hard no *for those
  services*. (This is specifically about the no-auth Lookout services — not a blanket
  rule against internet port-forwarding; purpose-built gear with its own design is a
  separate case, see below.)

**Name gotcha:** across the WAN you reach it by the box's **WAN IP + forwarded port**,
not `a.lan` — the friendly name is **LAN-only** (the box's dnsmasq only answers its own
clients; the upstream net's DNS doesn't know `a.lan`). Uplink mode is an IP:port story.

**If pursued:** consider adding simple auth to the map/rename endpoints before
exposing them anywhere beyond an island, and keep a bright line between "island mode"
(default, safe) and "uplink mode" (deliberate, trusted-net-only).

**Concrete use (Jim) — Telex RoIP across isolated LAN branches + the audio-drop for
Group Policy. PROVEN, not theoretical:** Jim already runs **Telex IP-223** RoIP across
the *public internet* via port forwarding — two unrelated ISPs (Kinetic Fiber ↔
Verizon), each router forwarding the IP-223's RTP port to the local box, with the
**far end's public IP placed in the IP-223's multicast Rx/Tx fields** so a LAN-multicast
device streams point-to-point across the internet (console site ↔ remote BK radio, no
VPN). Documented on his YouTube channel. So the WAN+port-forward topology isn't a
capability to consider — it's his established technique; the Lookout just adds a
map/data node to the same pattern. (His "never internet-WAN" caveat above is about the
*no-auth Lookout services*, not purpose-built RoIP gear built for this.) The
WAN/forward/firewall routing bridges **Telex IP RoIP** devices between isolated LAN
branches (segment them, forward only what you choose). Jim has also proven it over
**Starlink** (a Mini on a *business plan* for a routable public IP; voice RoIP needs
only **~32 kbps** in use, so it rides satellite fine) — also on his channel.

**Threat model (Jim's insight — "an AI hacking special with nothing to hack"):** an
IP-223 is a **dumb single-purpose appliance** — no OS, shell, filesystem or accounts —
so there is *nothing to hack* no matter how clever the attacker; the whole attack
surface is **inject or eavesdrop audio** ("spoof sounds"). Intelligence buys an
attacker nothing against a device that only moves audio packets. And that worst case
is the **same one RF already has** (anyone in range with a radio can key up on the
channel), so bridging RoIP over the internet changes the *geography* of the risk, not
its *class*. **Security by simplicity, not defense.** **Lookout caveat (be precise):**
the map service is likewise dumb/read-only (worst case: read the map or inject a fake
unit — still no system to pwn), BUT the Lookout runs on a real **Linux router**, so the
box's own admin/SSH *is* a "system" — the one genuinely intelligent-to-hack part. So
forward only the one dumb service, **never** the router admin, trusted nets only.

And at a
**Group-Policy-locked endpoint** where you can't drop in an IP/RoIP client, convert
**RoIP → plain analog audio** (a locked PC can always do audio in/out), patch through
it, then back to **RoIP** on the far side. **The principle:** audio is the universal,
un-blockable interchange for *radio* exactly as the browser is for the *map* — the
floor no lockdown reaches. The move is identical in both domains: **drop to the
lowest layer the policy can't touch, cross the boundary, climb back up.** It's the
project's core idea proven in a second domain (and Jim's earlier Teams+Telex patch is
the same radio↔audio↔IP pattern). Note the Lookout box's **USB sound card already
does mini-RoIP** (radio audio ↔ browser one way; the talk-back idea is the return
path), so a Lookout box could *be* an endpoint in such a design, not just a neighbor.

---

## Lookout QR Maker — add a minimal / bare-QR output option — *2026-11-20*

**Feedback (Jim):** the QR Maker forces the full placard on every card — the
"THE LOOKOUT" header, the "Scan with your phone camera…" caption, the "Box: ___"
write-in line, and the border — with no way to get just the code. For a clean short
address like `http://a.lan:8080/` the chrome is mostly redundant.

**The idea:** a toggle (or a second output) for a **bare QR** — just the code,
optionally with a small URL line under it — alongside the current full card. New
Maker version (bump + repackage per the standing rule).

**Bonus the address work already gives:** the shorter the URL, the lower-density and
cleaner the QR — `192.168.8.1:8080` (dense) → `a.lan:8080` (clean) → after the
port-flip `http://a.lan/` (cleanest). So the friendly-address thread makes the QR
prettier for free; a bare-output mode just lets that cleanliness show without the
furniture.

---

## Two removable drives — basemaps vs. situational content — *2026-11-20*

**The idea (Jim, "record this for testing"):** with a spare port on the hub, run
**two thumb drives** instead of one, split by job:
- **Drive 1 = basemaps** — the stable `.tpkx`/`.mbtiles` the map serves. Rarely
  changes; the greeter + whatever areas the box carries.
- **Drive 2 = "everything else, on a situational need"** — incident/situational
  content (docs, photos, reference, situational data — the Signal Shed content
  paths), swapped per incident.

**Why it's good:** physical separation of the **stable** layer from the **volatile**
layer. A crew **hot-swaps the situational drive** for a given incident — pull Drive
2, plug in that incident's Drive 2 — without ever touching the basemaps. Pure
removable-media, no GUI, fits the "name to order, nothing on the box" model.

**To test / resolve:**
- `units_kml` already scans `/tmp/mountd/*` for every `.tpkx`/`.mbtiles`, so **two
  drives' worth of maps already merge** into the Maps list for free — confirm it,
  and confirm a drive with **no** maps (Drive 2) doesn't choke the scan.
- **How Drive 2's non-map content is served** is the open design question: does
  `units_kml` serve arbitrary files from a mount, or does a small content server own
  Drive 2? This is the Signal Shed content-platform work (field-photo / content-lab
  paths) meeting the storage split. One server keyed by file-type (maps vs content)
  vs. two servers — decide on the bench.
- **Hot-swap behavior:** pull/insert Drive 2 mid-run — does the box notice the
  mount/unmount and refresh the list? (The `usb0` hotplug handler is the pattern.)
- **Label the sticks physically** so a crew never guesses which is which.

---

## The Lookout Traveler — a man-packable, battery Lookout — *2026-11-19*

> **→ Full record: [`docs/TRAVELER.md`](TRAVELER.md)** — platform decision, hardware,
> power design, the two configs (standard + battery-saving, with diagrams), the
> software deltas, and everything we learned (incl. why the phone can't host the
> radio). That doc is canonical; this entry is kept as the origin marker. Put new
> Traveler detail in TRAVELER.md, not here, so there's one source of truth.

The idea: the fully-wireless, walk-around Lookout — a battery-powered **GL-MT3000**
in a backpack, a **portable radio** as the relay, a **VK172 GPS** for "you are
here", and a **phone as the screen** (over Wi-Fi, or wired to save battery). It
carries the GPS-off-the-radio safety goal off the truck and into the fire: the
leader who walks a flank on foot keeps the whole live fleet in their pocket. Design
on record; **not built or proven yet** (MT3000 + parts arriving); not advertised
anywhere public. See TRAVELER.md.

---

## Field photo report — phone sends a pic back to the box — *2026-11-17*

**The idea (Jim):** the realistic reverse-path — not live video (that's the
moonshot at the end), just a **still photo or screenshot** sent from a phone
*to* the box. **Primary use case: a teacher (or any presenter) shares a photo
from her phone** — she sends it to the SSD and it's **quickly available from
the Maps drop-down list**, so anyone in the room taps it and views it. (The
same move also serves a field photo report — "washout on the north road"
plus a pic — but the everyday driver is sharing a picture to a room.)

**It's a shared board, not just a share (Jim):** the same mechanism makes it
**many-to-many** — *anyone* on the Wi-Fi can contribute a pic and it's
visible to everyone else right away (the picker's ~10 s refresh gives the
live feel for free). That's a **local, offline, no-account, no-app, cross-
platform shared photo board** — a combination that's genuinely hard to get
elsewhere (AirDrop is Apple-only; cloud albums need accounts + internet).
For a classroom it's also a privacy win: the pool never leaves the box, so
no cloud is harvesting a minor's photos. Posture: with many writers, trust =
whoever holds the Wi-Fi password (the joined group); fine for a controlled
room, no logins needed; lean harder on images-only + size/storage caps + the
isolated uploader, and consider an optional contributor name on each pic.

**How it surfaces — reuse the Maps dropdown (the key simplification):** the
content picker already scans the SSD and refreshes every ~10 s. An uploaded
photo drops into that *same* list as another selectable item — **no new
browsing UI.** Tap it and the browser just displays the JPEG (pinch-zoom
works natively; no tiling needed for a quick share — tiling is only for the
giant picture-worlds). The new parts are small: an upload endpoint that
writes the file to the SSD, and the list/viewer recognizing an image file as
a viewable entry alongside the maps.

**Why it's easy — easier than talk-back audio:**
- **No HTTPS wall.** Live mic/camera need `getUserMedia` (a secure context),
  which is blocked on the box's plain http. A **photo upload uses a plain
  file input** (`<input type="file" accept="image/*">` — optionally
  `capture` to open the camera, or just pick from the gallery), which works
  over ordinary http. The reverse-image path walks right past the wall that
  stops reverse-audio.
- **No encoding, no bandwidth ceiling.** A phone photo is already a
  compressed JPEG (a few MB); a one-time POST the router handles without
  noticing. None of the video headaches.

**Storage target = the map SSD (Jim's call), not the router's flash:**
- **Capacity** — internal flash is tiny (OS only); the SSD has tens to
  hundreds of GB.
- **Flash durability** — writing user uploads to the router's overlay flash
  invites wear and the sync-to-commit landmine we hit with audio; the SSD is
  built for writes.
- **Portability / stateless box** — the SSD already carries the maps
  (`units_kml` serves from `/tmp/mountd/*`). Photos live beside them, travel
  with the drive, and get pulled off after an incident by just taking the
  SSD. The router stays stateless firmware; the SSD is the data volume. Fits
  the "no default map, the SSD carries everything" design.

**Implementation notes / honest caveats:**
- **The SSD must be present AND writable.** No SSD (the "no maps found"
  state) = nowhere to store; disable upload and say "insert an SSD." The
  live SSD was **NTFS** — writing NTFS/exFAT on OpenWrt needs `ntfs-3g` /
  exfat write support, and a map mount may be read-only for safety, so the
  uploader needs a read-write mount. Flag this early.
- **Dedicated folder + storage cap.** Put uploads in e.g. `<drive>/photos/`,
  named by timestamp (+ optional unit / caption). Cap the size or rotate by
  date so photos can't fill the drive and starve map serving — tiles are the
  priority.
- **Removal resilience.** If the SSD is pulled mid-upload, fail gracefully
  (SSD-yank resilience already matters for tile reads).

**Posture shift — write it down:** this is the **first feature where a phone
*writes* to the box** — read-only becomes read/write. Still offline, still
on the island, nothing leaves. But anyone on the shared-password Wi-Fi can
post, so: **images only, size-capped, and keep the uploader its own isolated
process** (same wall as the audio streamer) so it can never touch the map,
the feed, or the audio.

**The video moonshot (separate — not this):** live video *could* relay
through the box the way audio does — but only if the **source encodes** it
(a camera/drone/phone outputting H.264/MJPEG → box relays → browser decodes).
The box must **never** encode raw video (the router CPU can't). Browser
camera capture also hits the HTTPS wall, and bandwidth (megabits × many
viewers) is the real ceiling. MJPEG-over-HTTP is the simplest first version.
Parked as "possible, but the photo-back above is the thing to actually
build."

---

## Info kiosk — scan-to-open, any content, offline — *2026-11-17*

**The idea (Jim):** The Lookout + the printed QR card = a self-contained
**info kiosk**. Set the box somewhere, print the QR placard, and anyone who
walks up scans it and gets a local page on their own phone — no app, no cell
signal, no login, no internet. The content doesn't have to be a map.

**Two generalizations that make it a kiosk, not just a map server:**
1. **Audio is source-agnostic.** The sound card's input doesn't care what's
   plugged in — radio, an iPad, a mixer, a mic. Unplug the radio, plug in any
   player, and the box fans that audio out to every phone on its wifi: a
   local, offline, one-to-many broadcast. **Important and clean: this is NOT
   RF / "pirate" radio** — nothing is radiated as a broadcast signal, no
   spectrum, no FCC / Part-15 / license question. It's a WebSocket stream on
   a private wifi LAN — legally just a web page that plays sound. The limits
   are mundane: wifi range (a building or a lot, not miles), and ordinary
   content/copyright courtesy if you rebroadcast music you don't own.
2. **The served page can be anything.** Today the box serves `map.html` at
   `/`. A kiosk wants a small **landing / info page** instead (or in front of
   the map): text, images, the zoomable picture worlds, a "listen" button,
   and links to the map. A mini offline website on the box. Small addition,
   same mechanism — `units_kml.py` already serves files; the QR just points
   at `/`.

**Scenarios (any "everyone here, on their own phone, offline" space):**
trailhead / park kiosk (map + trail info + safety + audio guide); museum or
gallery (a picture world + narration); event info board (schedule, site map,
announcements); lobby directory; classroom station; and the strong one — a
**shelter / disaster info point**, which is offline *by design* exactly when
the grid and the cell network are down.

**Why it's a natural:** the pieces already exist — the QR Maker makes the
placard, the box serves files and audio, it's reboot-safe and runs on
nothing. The only new piece is a general landing page so the content isn't
locked to the map.

---

## Reverse audio — browser talk-back (a dispatch console) — *2026-11-17*

**The idea (Jim):** the USB sound card has an unused *output* path (its
headphone/speaker jack). We already move radio audio one way — card **in**
→ streamed **out** to browsers (`lookout_audio.py`). Run the same transport
backwards: a browser captures the mic, sends PCM to the box over a
WebSocket, and the box plays it out the sound card's output into the
radio's mic/line input. Result: **someone talks on the radio net from a
phone browser — no radio in hand.** The Lookout stops being a monitor and
becomes a two-way dispatch console.

**Why it's believable:** the transport is symmetric. The hard part was
learning to move raw PCM over a WebSocket with no codec; the direction is
free. Mirror the pieces:
- Browser: `getUserMedia` → Web Audio → Int16 PCM → WebSocket **to** the box
  (the exact inverse of today's playback path).
- Box: a small isolated streamer reads the WebSocket and writes to
  **`aplay -D plughw:0,0`** (the mirror of today's `arecord`). Own process,
  own port, zero shared state — same isolation wall as `lookout_audio.py`.

**The two things that make it more than a copy-paste (be honest about these):**
1. **Browser mic needs HTTPS.** `getUserMedia` only works in a *secure
   context*. Our map is served over plain `http://192.168.8.1:8080`
   ("Not secure"), and only `localhost` is exempt from the secure-context
   rule — a bare LAN IP is not. Audio **playback** (what we ship today)
   works fine on http; **mic capture does not.** So talk-back needs the box
   to serve https (a self-signed cert → browser warning the user clicks
   past), or some other secure-context trick. This is the real blocker, not
   the audio.
2. **Keying the radio (PTT).** Feeding audio into a mic input does **not**
   transmit — the radio has to be *keyed*. Two ways: **VOX** (radio keys
   itself when it hears audio on the input — no extra hardware, simplest
   path) or a real **PTT line** (a GPIO / USB-serial RTS pin, cleaner and
   no VOX tail/clipping). Plus a small **level pad**: a headphone output is
   ~1 V, a mic input wants millivolts, so a resistor divider in between or
   it'll be distorted/overdriven.

**The bigger implication (design + judgement, not code):** this crosses from
*passive listen* (read-only, clean, nobody can tell it's there) to *active
transmit*. That's a different posture entirely — now the box can key a
transmitter: who's allowed to talk, accidental/stuck keying, and the
licensing/FCC reality of the radio it's wired to. The receive side asks
nothing of anyone; the transmit side is a real operational decision. Worth
building the UI so transmit is deliberate (a clear press-and-hold "talk"
control, never VOX-open-by-default), and worth deciding *who* gets the
talk-back link vs. the plain map link.

**Keep the isolation rule:** a talk-back streamer is its *own* process on
its *own* port, like `lookout_audio.py` — so transmit up/down never touches
the map, the position feed, or the receive audio.
