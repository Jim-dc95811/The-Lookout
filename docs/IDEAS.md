# The Lookout — Journal of Ideas

Captured ideas for later, not built yet. Newest first. An entry here is a
direction to weigh, not a committed plan.

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
