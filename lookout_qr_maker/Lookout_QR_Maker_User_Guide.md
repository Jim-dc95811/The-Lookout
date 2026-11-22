# Lookout QR Maker

Make a printable QR card that gets a phone onto the Lookout map — the map address, the Wi-Fi, or both on one card.

> **Installing Lookout QR Maker — read this first**
> - Right‑click the downloaded zip and choose **Extract All** before using it.
> - Open the folder and double‑click **`Make a QR card.bat`** — that one file is all you click.
> - If Windows shows a blue "Windows protected your PC" notice, click **More info → Run anyway**.
> - The first time, it installs one small graphics helper (Pillow) by itself — let it finish.
> - Then the Lookout QR Maker window opens. Nothing else to set up, and it never needs the internet.

A printable copy of this guide is **Lookout QR Maker.pdf**, right next to the `.bat`.

---

## What it's for

A crew points a phone camera at a printed sticker and they're on the live map — **no app, no typing, no login, no GIS.** The QR Maker builds the card. It can make three kinds, chosen from the **"What should the card do?"** dropdown:

- **Open the map** — the QR opens the Lookout map in the browser.
- **Join the Wi-Fi** — the QR joins the box's Wi-Fi network (no typing the name or password).
- **Join + open (one card)** — both codes on one card: **① join the Wi-Fi, ② open the map.** The complete, zero-typing onboarding sticker.

![An example Lookout QR card — point a phone camera at it and tap the banner to open the live map](../images/lookout_qr_card.png)

## How to use it

Pick a mode in the dropdown, fill in the fields it shows, click **Make QR card**. The card saves to your Desktop as a `.png` and opens so you can see it. Print it on any printer — it scans cleanly at business‑card size or larger.

**Open the map** — in **Map address**, type the full address the QR should open: for the Lookout that's **`192.168.8.1:8080`** (include the `:8080` — it's the port the map serves on). It encodes exactly what you type, adding only the invisible `http://` so the scan opens cleanly.

**Join the Wi-Fi** — enter the box's **Wi-Fi name** (SSID) and **Wi-Fi password**. Tick **Open network** if it has no password, or **Hidden network** if the SSID isn't broadcast. The card's QR is the standard Wi-Fi‑join code a phone camera reads to connect.

**Join + open** — enter the Wi-Fi name, password, *and* the map address. You get one card with both codes, numbered ① and ②.

Tick **Just the QR code (no card)** on the map/Wi-Fi modes if you want the bare code with no banner, to drop into your own sticker or sign.

## Getting a crew phone onto the box (once per phone, then automatic)

With a **Join + open** card:

1. **Scan ①** → the phone offers to add and connect to the box's Wi-Fi → accept.
2. If the phone warns **"network has no internet — stay connected?"** → say **Yes / Always.** The box has no internet by design; this keeps the phone from dropping it for cellular.
3. Turn on **Auto-connect** for that network (in the phone's Wi-Fi network details). From then on the phone rejoins the box automatically whenever it's in range — no re-scanning.
4. **Scan ②** → the map opens. (Bookmark it and it's one tap next time.)

That's it — one card, one time, and the phone is a Lookout display forever after.

**Re-testing on your own phone?** A phone that has *already joined and saved* the network will not act on a Wi-Fi‑join scan — it looks like nothing happens, because there's no new network to join. **Forget the network first**, then scan. (A fresh crew phone that's never seen the box doesn't have this problem.)

## Good to know

- Scan with the phone's normal camera app — no special QR app needed. (A few budget Android cameras don't handle Wi-Fi‑join codes from the plain camera; on those, scan from **Settings → Wi-Fi → the QR/scan icon**.)
- The Wi-Fi code uses the same `WIFI:` format phones generate themselves, so it joins the same way your phone's own "Share Wi-Fi" does.
- The **Wi-Fi name must match the box's broadcast network exactly** — same spelling, case, and spaces.
- Works for any address or network up to **78 characters**.
- Because every Lookout/Traveler uses the same address, one **map** card works for every box.

## What's in the folder

- **`Make a QR card.bat`** — double‑click this
- **`Lookout QR Maker.pdf`** — this manual
- **`System Files`** — the program; leave it alone
- **`Lookout_QR_<name>.png`** — the card it makes, on your Desktop

---

*Part of **The Lookout** — a plug‑in box that puts live units and offline maps on any phone or PC, with nothing installed on the viewer. Free, offline, open. https://github.com/Jim-dc95811/The-Lookout*
