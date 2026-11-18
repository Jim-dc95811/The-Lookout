# The Lookout — Security Analysis

> *The safest router in the world is the one with the empty WAN connector.*

*An honest, upfront account of what The Lookout does on a network, what it
does not do, and how to verify every claim in this document for yourself.*

This report is written to be handed to a security or IT team. It is not a
"don't ask, don't tell" device. The whole point of this page is the
opposite: here is exactly what it is, here is what you will see in your
logs, and here is how to prove it does what I say — with your own tools, not
my word.

---

## In plain language (for leadership)

The Lookout is a small travel router — the same kind you'd take on a trip —
that has been set up to do one job: serve a map, live unit positions, and
radio audio to any phone or PC **on its own private Wi-Fi**, with **no
internet connection at all**.

The simplest way to picture it: your phone joins a small, self-contained
building and never leaves it. It is never redirected, never sent anywhere
else, never asked to sign in to anything. The map it shows comes from a
server **inside that same building** — the manager's office downstairs. You
walk down to get a map; the box never comes to you, never follows you home,
and has no phone line to the outside world to leak anything through.

Three things a reviewer should take away:

1. **It does not spoof or impersonate any of your equipment.** It is
   conspicuously its own device, with its own name and its own network. It
   never pretends to be your Wi-Fi, your gateway, or a trusted company
   device.
2. **It has no path to the outside.** No internet, no cloud, no accounts, no
   "phone home." Nothing a device shows it can leave the box.
3. **You will see the router in your logs, and that's on purpose.** It's
   mine, it's disclosed here, and I'm glad to show IT precisely why it's
   safe.

---

## What The Lookout is

- A single **GL-MT6000 travel router** running **OpenWrt** (standard,
  unmodified router firmware), used exactly the way its makers intend.
- It broadcasts **its own Wi-Fi network** with its own name (for example
  `GL-MT6000-xxx`) and its own password. It is a separate island, not joined
  to any agency network and not connected to the internet.
- On that island it runs three small programs that **serve** content to a
  web browser: the map and live units, the radio audio, and a position
  feed. Nothing is installed on the viewer's phone or PC — they just open a
  web page.
- Full detail of everything added on top of the stock router — every driver,
  library, and program, each with its job — is in the companion document
  **The Lookout — Beyond Factory**. Everything was installed through
  supported channels; no firmware was rebuilt and no custom kernel was used.

---

## Upfront disclosure: you will see it in your logs

If a device that also touches your network has ever been near The Lookout,
its router may appear in your connection or Wi-Fi logs. **This is expected
and disclosed, not hidden.** Here is what that entry is:

- A device named like **`GL-MT6000-xxx`** (a GL.iNet travel router) with its
  own hardware (MAC) address.
- It is **mine**, set up as The Lookout, described in this document.
- In normal use, phones and PCs join **The Lookout's own Wi-Fi** — they are
  on its island, not your network — so the two environments stay separate.

If you see it and want to ask about it, please do. That is the intended
reaction. I would rather you flag an unknown router and have me explain it
than have anything about this be quiet.

---

## It does not spoof or impersonate your equipment

This is the concern a security team raises first about any unknown wireless
device, so it is answered first and plainly. The Lookout:

- **Uses its own distinct Wi-Fi name.** It does **not** broadcast a network
  that mimics or duplicates any agency SSID. It is not an "evil twin."
- **Uses its own MAC address.** It does **not** spoof or clone the hardware
  address of any trusted device.
- **Does not impersonate your gateway, DNS, or services.** It is the gateway
  of **its own** private network only; it makes no claim to be anything on
  your network.
- **Does not present itself as a managed or corporate device.** It is openly
  a travel router.
- **Collects no credentials.** There is no login page, no sign-in, no form
  that asks for a password of any kind. It cannot harvest what it never
  asks for.

In short: it is conspicuously, deliberately **itself**. Nothing about it is
disguised as something it isn't.

---

## Security posture — how it's built

The design follows one rule everywhere: **be a passive service you choose to
visit, never an active agent that acts on you.**

- **Pull, not push.** The box never grabs your attention. There is no
  captive portal, no redirect, no auto-opening page, no "sign in to this
  network" pop-up. You reach the map by deliberately scanning a QR code or
  typing the address. The user always initiates; the box only ever answers.
- **Serve-only — it listens, it never initiates.** The three programs wait
  on fixed ports and respond when a browser connects. The box makes **no
  outbound connections of its own** — not to your device, not anywhere.
- **An offline dead-end island.** The Lookout has **no internet uplink**. It
  cannot phone home, cannot be used as a stepping-stone to the internet, and
  cannot send data anywhere, because there is nowhere for data to go.
- **Client isolation.** Devices on The Lookout's Wi-Fi are kept from seeing
  **each other**, so joining it does not expose your phone to other phones
  on the network. The only thing on the island to talk to is the one map
  server.
- **Two separate layers.** The ordinary router housekeeping (handing out
  addresses, answering "who's there") is stock OpenWrt — standard plumbing
  that every router does. The map, units, and audio are three small, plain
  programs that sit on top and only wake when visited. The housekeeping and
  the application are different software; neither reaches outward.

---

## Trust model

Networking has always rested on one assumption: once you join a network, you
must be able to reach your own gateway — that's how any device gets an
address and does anything at all. Opening the map is exactly that: your
browser reaching a server on the network you chose to join. That is the most
basic, least-privileged operation there is, which is why it works even on
tightly managed devices (see below).

The Lookout is also compatible with a stricter, "**trust nothing**" (Zero
Trust) posture — because it **asks for no trust**. A Zero-Trust network
worries that a hostile local device will pivot into your equipment or
exfiltrate data. The Lookout cannot: it has no internet to escape through,
makes no outbound connections, isolates its own clients, and holds no
account or credential. It is a dead-end vending machine you walked up to. It
makes no demand to be trusted, so there is nothing to grant and nothing to
betray.

---

## The realistic threat model

Good security starts with an honest picture of who is actually on the
network. In normal use, the people who join The Lookout are the operator and
their own group — a crew, a class, staff — non-technical users who are there
to see a map, not to attack a box. For that population the practical risk is
**accidental misuse, not intrusion**: a malformed upload, a fumbled request,
an odd input. The box is built to **tolerate** that the way good electronics
tolerate a voltage spike — with size and type limits, process isolation, and
graceful failure — not to wage a security war against its own users.

At the other extreme, a determined, sophisticated attacker deliberately
targeting a specific device is a threat **no consumer product fully stops** —
the same is true of any router, phone, or appliance on the market. What this
design does against that tier is **remove the paths such an attack needs**:
with an empty WAN connector there is no remote reach in or out, the box
initiates no connections of its own, and it runs no services that chase the
internet. You cannot remotely attack, command, or exfiltrate from a device
that has no path to you and makes none to anyone.

In short: the realistic user is harmless by capability, and the box is built
to shrug off their mistakes; the unrealistic super-attacker is stopped by no
vendor anywhere, and is given nothing here to work with.

## What is added on top of the stock router (attack surface)

The only software added beyond standard OpenWrt is three small programs
written in plain Python (standard library only), each listening on one port:

| Program | Port | What it does |
|---|---|---|
| Map server | 8080 | Serves the map, the live units, and the map tiles |
| Audio streamer | 8081 | Streams the radio audio to the browser (receive only) |
| Position feed | 10110 | Offers the clean position feed to mapping apps |

They are separate, isolated processes. None of them opens a connection
outward; all they do is answer requests that arrive. There are no added
background services that reach out, no telemetry agents, and no cloud
clients. The full inventory is in **The Lookout — Beyond Factory**.

---

## Data handling

- **No telemetry, no analytics, no cloud, no accounts.** Nothing is reported
  to any vendor, including me.
- **The imagery and the radio positions are the operator's own data.** They
  live on removable media and in the box's memory, and they **never leave
  the box** — there is no connection over which they could.
- **The audio is receive-only.** The box listens to a radio and relays that
  audio to browsers on its own Wi-Fi. It does not transmit, and nothing a
  listener does is sent back out.

---

## Proven on a locked-down government device

The Lookout has been run live on a **government-issued iPhone under Mobile
Device Management (MDM) and Group Policy lockdown** — among the most
restricted devices in normal service. It joined The Lookout's Wi-Fi, opened
the map in the browser, showed live units, and played the audio, with
**nothing installed** on the phone. The device's management policies raised
no obstacle, because opening a local web page you navigated to is ordinary,
permitted browser behavior — there is no app to vet, no internet to filter,
and no content leaving the device.

---

## Verify every claim yourself (please do)

Do not take my word for any of this. The strongest part of this report is
that it is **falsifiable** — here is exactly how to test it with your own
tools.

**The capture.** On a laptop, join The Lookout's Wi-Fi, **unplug/disable any
other internet connection**, and run a packet capture (e.g. Wireshark) on
that Wi-Fi adapter while you use the map.

**What you will see — and it is normal:** your *own* devices are noisy.
Windows will fire its connectivity checks (NCSI), ARP requests repeat
constantly, and whatever apps are installed will keep trying to call home.
**All of that is your device, not The Lookout** — it is your own operating
system and apps reaching for an internet that isn't there, and failing.
Those failures are themselves evidence: there is no way out of the island.

**What you will not see:** the box initiating any connection to the outside
world. To prove it in one line, apply this display filter:

```
ip.src == 192.168.8.1 and not ip.dst == 192.168.8.0/24
```

That asks Wireshark to show **any packet the box sent toward anywhere
outside its own local network.** It returns **empty**. The box never tries
to leave the building. Pair that with a capture filtered to
`ip.addr == 192.168.8.1` to see the only conversation it does have: serving
your map.

(The box's address is shown at the bottom of the map page — commonly
`192.168.8.1`; substitute the address you actually see.)

---

## Honest limitations

A security document that lists no limits isn't honest. Here are the real
ones:

- **A force-tunnel VPN laptop may not reach it.** A managed laptop
  configured with an always-on VPN that tunnels **all** traffic (including
  local) with local-network access disabled will send even a request to the
  box into the corporate tunnel, where it can't reach the local Wi-Fi. In
  that case the map simply won't load — nothing is bypassed or broken; the
  device just can't see the box. The primary use is phones, which are not
  affected this way.
- **The Wi-Fi password is shared.** Everyone who uses the box knows the Wi-Fi
  password, so the network should be treated as semi-public. That is exactly
  why the box is built serve-only with client isolation: so a shared network
  still exposes nothing.
- **Physical control matters.** As with any appliance, whoever holds the box
  controls it. It is the operator's responsibility to keep physical custody
  and to be responsible for the imagery and radio data loaded onto it.
- **Receive-only today.** The audio feature is listen-only. If a two-way
  "talk back" capability were ever added in the future, that would change
  this posture (it would then transmit), and it would get its own analysis
  before any such change shipped.

---

## The bottom line

The Lookout does not spoof your equipment, does not impersonate your
network, does not install anything on any device, and has no path to the
outside world. It is a passive, offline, self-contained map server that you
choose to visit — and every statement in this document can be verified with
a packet capture in a few minutes.

It is disclosed to you on purpose. You will see the router; now you know what
it is and why it's safe. Questions and audits are welcome — that's the point.

*— Jim*
