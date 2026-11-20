# How BK Delivers GPS Data — and where The Lookout taps it

*Reference note. Pulled together from BK's own materials, the wildfire-agency
(NIFC/NIICD) operational docs, the LocateONE Lite launch materials, and what we
proved on the bench (radio → USB → feed). Written 2026-11-20.*

BK's GPS delivery splits into **two domains**: how positions travel **between
radios** (over the air), and how they get **off a radio onto a screen** (the
gateway). The Lookout lives entirely in the second domain.

---

## 1. Over-the-air (radio → radio / network)

How a position moves through the radio system itself. The payloads here are
proprietary P25 location formats — which is exactly why The Lookout does **not**
decode the RF and instead taps the gateway (§2).

- **Manual** — radio displays its own fix; operator sends it with PTT.
- **P25 Location Services — Tier 1** — location sent to a specific **Unit ID**
  over a P25 conventional channel; All-Call ID `16777215` broadcasts to all P25
  radios. Radio-to-radio.
- **P25 Location Services — Tier 2** — location sent to an **IP server** over a
  P25 trunked/conventional network. Infrastructure-based.
- **Peer-to-peer** — location rides **inside every voice transmission** (ANI in
  analog, the low-speed data channel in P25). *This is the `$PP25` data The
  Lookout reads.* Receiving radios can show the sender's lat/lon or bearing +
  distance.
- **FAST data messaging** — a data burst carrying MYID, hardware ID, and location.

---

## 2. Off-the-radio → computer / phone / map (the gateway — The Lookout's territory)

A designated **base/donor radio** receives everyone's positions and re-serves
them to software. BK does this three ways:

### 2a. USB-network path → `pkgcot.exe` → Google Earth / WFTAK / EGP
BK's **own primary computer delivery**, and the *exact* connection The Lookout's
`bk_bridge` taps. The NIFC/NIICD doc spells out the chain:

> base radio → **BK USB cable + interface dongle + BK USB driver** → `pkgcot.exe`
> → writes a **KML** link file → **Google Earth Pro** Network Link refreshes
> every 4 s. Also forwards to **WFTAK** (Wildland Fire Team Awareness Kit) and
> **EGP** (Enterprise Geospatial Portal), which require accounts. Labeled
> **Beta / test-and-eval only**.

**BK's docs never name the data format.** We proved it on the bench:
**RNDIS over USB, TCP `:65535`, subscribe `80 04 18 e4 81`, streaming
`$GNGGA` + `$PP25,<unit_id>` NMEA.** The reverse-engineering filled in exactly
what BK doesn't publish.

### 2b. LocateONE (full)
A donor radio feeding a server-side "location data engine." Enterprise /
infrastructure scale.

### 2c. LocateONE Lite
Software-only **ATAK plug-in** over **Bluetooth** to an Android phone, off-grid
(launched March 2026). This is the newest path — and the one we hit the wall on
2026-11-20. It is **deliberately closed and likely licensed** (ATAK-bound). Our
full probe of the radio's Bluetooth (BLE register map + classic RFCOMM HCI
capture via btvs/Wireshark) confirmed the position never flows to a generic
client — it's gated behind LocateONE's own handshake. See the session notes /
The-Signal-Shed for the capture detail.

---

## 3. Formats at each step

| Step | Format |
|---|---|
| Over-the-air | Proprietary P25 location (Tier 1/2), ANI / low-speed data, FAST |
| Base radio USB output | **NMEA `$GNGGA` + proprietary `$PP25,<unit_id>`** over RNDIS/TCP (reverse-engineered; BK publishes none of it) |
| To the map | KML (Google Earth Network Link), or ATAK CoT (LocateONE Lite) |

---

## 4. What this means for The Lookout

1. **The USB approach taps BK's own gateway** — the same base-radio-over-USB
   connection `pkgcot.exe` uses. The Lookout is effectively an **open, offline,
   browser-based `pkgcot.exe`** — no Google Earth, no accounts, no beta label.
2. **The format (`NMEA + $PP25`) is unpublished by BK** — obtained by
   reverse-engineering. That's genuinely the only open route in, not a shortcut
   around a documented API.
3. **There is no public BK location API or SDK.** Even the 3AM Innovations / BK
   partnership (FLORIAN) gives zero integration detail — a private arrangement.
   Third parties either license BK's software or reverse-engineer the gateway.
4. **The Bluetooth / LocateONE Lite path is intentionally sealed** (a product,
   not an interface). That's the wall; not worth more effort. Don't re-chase it.
5. **Strategic read:** BK funnels everything to *their* consumers (pkgcot +
   Google Earth, LocateONE, ATAK). The Lookout is the **open alternative to all
   three** — same gateway, modern / offline / any-phone-browser, no license.
   The research validates the whole direction.

---

## Sources

- BK — *GPS Features of BKR Series Radios*: https://www.bktechnologies.com/service-portal/edu_details/8
- NIFC/NIICD — *GPS Messaging V4* (the pkgcot operational chain): https://www.nifc.gov/sites/default/files/NIICD/docs/NIICD%20GPS%20Messaging%20V4.pdf
- BK — *LocateONE Lite launch* (ATAK/Bluetooth, off-grid): https://rallies.ai/news/bk-technologies-launches-locateone-lite-for-off-grid-atak-location-via-bkr-radios
- *3AM Innovations × BK Technologies* (FLORIAN, no integration detail): https://www.criticalcommunicationsreview.com/ccr/news/118969/3am-innovations-partners-with-bk-technologies
- CISA / SAFECOM — *GPS for Public Safety Location Services*: https://cisa.gov/sites/default/files/2024-08/safecom_ncswic_gps_for_public_safety_24_0814_final_508c.pdf
