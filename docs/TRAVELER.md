# The Lookout Traveler — design record

*The man-packable, battery-powered Lookout. This file is the **consolidated
archive** for the Traveler — hardware, power, the two configs, and what we've
learned — so none of the design work lives only in chat or memory. Non-public: it
sits in the repo docs but is **not advertised** anywhere (README, site, family
storefront).*

> **STATUS — 2026-11-20: DESIGN ON RECORD. NOT BUILT. NOT PROVEN.** Hardware is
> arriving (MT3000 + PD power bank + VK172 GPS due ~2026-11-20/21); nothing is
> bench-tested yet. It graduates onto the public storefront only after a real box
> is provisioned and a phone pulls the live map off a battery pack — the standing
> "proven workers first" rule. Until then this doc is the memory.

---

## What it is

The fully-wireless, walk-around Lookout. A battery runs the brain (a **GL-MT3000**
travel router); a **portable radio** on its own battery is the relay; a small GPS
gives "you are here"; a **phone is the screen** over the box's own Wi-Fi (or wired —
see configs). Put it in a backpack and it tracks the whole fleet as the operator
walks the incident. The fixed Lookout rides in a vehicle or on a bench; the
Traveler rides on a back.

**The use case that sells it:** the leader who leaves the truck to actually lead —
pushes a line, walks a flank on foot — normally goes *blind*, because the display
stays in the cab. The Traveler puts the whole live picture in their pocket: every
unit the system can hear, while they move. It's the GPS-off-the-radio safety goal
(the "Holy Grail") un-bolted from a vehicle and carried into the fire. Coverage is
the **repeater footprint**, not line-of-sight — the relay just needs clean copy of
the repeater, so a stubby is fine; the network does the long haul.

**Theme:** single user, strip off every part that draws power, use the smallest
pieces that do the job. The map is the whole job.

---

## Platform — GL-MT3000, not the Pi

Decided 2026-11-20. The Traveler is built on the **GL-MT3000 Beryl AX** — the same
OpenWrt/GL family as the fixed Lookout (MT6000), so it's **one platform for both
boxes**: everything proven on the MT6000 (`bk_bridge`, `units_kml`, the one-click)
carries straight over, same code.

The Pi was weighed hard — lower power (~3–5 W vs ~7–9 W), four USB ports (no hub
needed), native ALSA audio, plain-NMEA USB GPS — and **parked**. The deciding
reason: the **GL is self-serve** — a buyer stands it up alone with the manual + one
button — while the **Pi needs AI assistance** to set up (flash, hostapd,
hardening). That self-serve line is the whole product. The MT3000 (512 MB RAM —
huge headroom, the stack measures ~23 MB; Wi-Fi 6; ~$84) is plenty for the light
load. **The Pi's real home is the Signal Shed bench, not the product.**

The one consequence of the GL: it has **one USB port**, so the Traveler carries a
**powered hub** (below) to fan out to radio + GPS + storage. The Pi's four ports
would have avoided it.

---

## Physical build — two configs

### Standard (phone on Wi-Fi)

![Traveler — standard config](../images/the_traveler_standard.png)

Phone joins the box's **Wi-Fi**. Radio → **powered USB hub** → the router's single
USB3 port (**data only**). The hub is self-powered off the 5 V rail (its own
17 W / 2.5 A input via a USB-C pigtail) and carries the radio + **VK172 u-blox GPS**
+ thumb drive(s) downstream, so the one router port never sources their current.
Donor radio = **BKR9000** handheld **or** **KNG-M150** mobile.

### Battery-saving (phone wired, Wi-Fi off)

![Traveler — battery-saving config](../images/the_traveler_battery_saving.png)

Router **Wi-Fi radio off** (the slashed antenna) and the phone wired in through a
**USB-C→Ethernet adapter** on the LAN port. This kills **both** Wi-Fi radios — the
box's AP (one of the steadiest draws in the whole unit) and the phone's — the
biggest single power saving, and gives a rock-steady wired link with no RF
congestion. It also unlocks a **Wi-Fi-less / LTE-less tablet** as a pure display.
This is the **supported** side of Android USB networking: a phone *hosting* a
standard Ethernet adapter is adopted as `eth0` natively — the opposite of reading
an RNDIS gadget, which Android can't do (see "What we learned"). If the phone needs
charging while wired, use an adapter with **USB-C PD pass-through**.

---

## Hardware

| Part | Role | Notes |
|---|---|---|
| **GL-MT3000 (Beryl AX)** | the brain / Wi-Fi + USB host | 512 MB RAM, Wi-Fi 6; runs the same stack as the MT6000 |
| **Portable radio** — BKR9000 handheld **or** KNG-M150 mobile | the relay (donor radio) | on its own battery; USB = data link (RNDIS), near-zero draw from the box |
| **Powered USB hub** (SABRENT 4-port) | fans the one router port out to radio + GPS + storage | self-powered, 17 W / 2.5 A input fed from the 5 V rail |
| **VK172 u-blox GPS** | "you are here" | serial NMEA — rides `gps_source.py`'s serial branch, no Garmin/libusb path |
| **PD power bank** | the pack | single 5 V rail; USB-C pigtails feed router + hub |
| **USB-C→Ethernet adapter** (UGREEN) | battery-saving config only | phone as host → `eth0`; get the PD-passthrough version if charging while wired |
| **Thumb drive(s)** | map / content storage | optional two-drive split: basemaps vs. situational (see `IDEAS.md`) |
| **Cudy AX3000 AP** (optional) | Wi-Fi range boost | run in **AP / bridge** mode, not router mode |

---

## Power design

- **Single 5 V rail.** Buck output and the battery share one node; an on/off switch
  gates that node; the switch output feeds the GL **and everything else**. There are
  **not** dual 5 V rails — one rail, multiple taps.
- **The hub carries its own power.** It's a *powered* hub (17 W / 2.5 A input), fed
  off the rail via a USB-C pigtail — so the router's one USB port does **data only**
  and never has to source the radio/GPS/drive current. (A hub's "900 mA combined"
  spec note is its *bus-powered* fallback — irrelevant with the adapter in.)
- **Current budget is nowhere near tight.** Radio is self-powered (USB ≈ 0 draw),
  VK172 ≈ 40 mA, a thumb drive ≈ 150 mA on read — a couple hundred mA against the
  hub's 2.5 A. The real rail load is the router itself.
- **Runtime (ballpark — confirm with an inline watt meter):** GL build ≈ 7–9 W for
  the router + the hub's downstream. A ~150 Wh pack ≈ a full shift; ~72 Wh ≈ half;
  ~240 Wh ≈ two shifts. Battery-saving config (Wi-Fi off) extends all of these.

---

## Software — deltas from the fixed Lookout

Same brain (`bk_bridge` + `units_kml`), three small differences:

1. **GPS = VK172 serial NMEA.** `gps_source.py` auto-detects Garmin-libusb → gpsd →
   **serial NMEA**; the VK172 drops onto that third branch. "You are here" comes
   along for free. (No Garmin D800/libusb path on the Traveler.)
2. **Battery-saving config = Wi-Fi off + wired client.** Disable the AP radio; the
   phone/tablet reaches the map over the LAN port through a USB-C→Ethernet adapter.
3. **No audio.** The operator *wears* the portable and listens to its own speaker,
   so the Traveler drops `lookout_audio.py` and the USB sound card entirely. Lighter,
   fewer parts, one less thing to configure.

---

## What we learned (so it's never re-derived)

- **The phone can't host the radio.** Android's framework won't adopt a USB **RNDIS
  gadget** (`usb0`-style) as a network interface — it only takes `eth\d`-named
  interfaces — and apps can't bring one up without root. Researched 2026-11-20
  across every analog (PlutoSDR→Android, single-board→tablet): **nobody has cracked
  generic RNDIS-on-stock-Android.** The ones who "got it working" reconfigured their
  device to ECM, rooted it, or reversed roles. → **The router (USB host) is
  irreducible.** This is *why* the box exists.
  - Note the clean distinction: a phone *hosting* a normal USB-C→**Ethernet adapter**
    (battery-saving config) is the **supported** case and works natively. Reading an
    RNDIS gadget is the unsupported one.
- **How BK delivers GPS → [`docs/BK_GPS_DELIVERY.md`](BK_GPS_DELIVERY.md).** The
  Lookout taps BK's own base-radio-over-USB gateway (the `pkgcot.exe` path), format
  reverse-engineered (`NMEA + $PP25`). No public BK API/SDK.
- **BK Bluetooth / LocateONE Lite is sealed.** Full probe of the radio's BLE +
  classic RFCOMM (btvs/Wireshark HCI capture) confirmed position never flows to a
  generic client — it's gated behind LocateONE's handshake. **Don't re-chase it.**

---

## Open / to prove (build order when the MT3000 lands)

1. **Poke the bare MT3000** first — firmware, USB host behavior, where the one port
   enumerates the hub.
2. **VK172 through `gps_source.py`'s serial branch** — confirm the NMEA dongle is
   picked up and plots "you are here."
3. **Standard config** — hub brings up the radio's `usb0` through the one host port;
   `bk_bridge` + `units_kml` serve the map over the box's Wi-Fi to a phone.
4. **Battery-saving config** — Wi-Fi off + USB-C→Ethernet client comes up as `eth0`
   and pulls the map over the wire.
5. **Real battery-runtime measurement** with an inline watt meter, both configs.
6. **Two-thumbdrive split** (basemaps vs. situational) — see `IDEAS.md`.

Then decide whether it graduates onto the README/site as the second body in the
product line: **The Lookout** (MT6000, vehicle/mains) + **The Lookout Traveler**
(MT3000, battery, man-packable) — same brain, two bodies.

---

## Cross-links

- **Origin idea + narrative:** [`docs/IDEAS.md`](IDEAS.md) (the Traveler entry).
- **BK GPS delivery:** [`docs/BK_GPS_DELIVERY.md`](BK_GPS_DELIVERY.md).
- **The fixed Lookout:** [`README.md`](../README.md), [`docs/DEVELOPERS_GUIDE.md`](DEVELOPERS_GUIDE.md).
