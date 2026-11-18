# Lookout Manager — User Manual

> **Installing Lookout Manager — read this first**
> - **Extract All** first (right-click the download → *Extract All*), then open the extracted folder.
> - Double-click the one file: **`Start Lookout Manager.bat`**. Everything else lives under **System Files** — leave it alone.
> - Windows may warn (unknown publisher). Click **More info → Run anyway** (or, on the zip, *Properties → Unblock* first).
> - The launcher gets your PC ready: it finds Python (installs it if missing — answer **Y**, no admin needed) and installs the one library it needs (`paramiko`, for SSH).
> - Lookout Manager sets up and manages **The Lookout** — a GL-MT6000 travel router that serves your live units. You need that router (and the radio) for it to do anything.

A printable copy of this guide is **Lookout_Manager_User_Guide.pdf**, right next to the `.bat`.

---

## What it is

Lookout Manager is a small Windows app that stands up and maintains **The Lookout** — the travel router that reads your P25 radio and serves live units to any browser, phone, or ArcGIS Earth. It has two tabs:

- **Set up a router** — turn a brand-new router into a Lookout in one click.
- **Name units** — give your unit IDs friendly names that show on the map.

## Set up a router (one click)

1. **First‑boot the router and update its firmware.** On the router's own page (`http://192.168.8.1`), set an admin password and confirm it has internet, then **install the firmware update it offers and let it reboot** — do this *before* anything else. The Lookout is proven on current GL firmware; don't set up on whatever shipped in the box. (One time only — the box never needs the firmware touched again.)
2. Connect your PC to the router (its Wi‑Fi or a LAN cable). The router must have **internet** for this one‑time setup.
3. Open Lookout Manager and go to the **Set up a router** tab.
4. **New router IP** — usually `192.168.8.1` (the GL‑MT6000 default). **Admin password** — the router's own admin password (the one you set on the router's first‑boot page).
5. Click **Set up this router** and watch the log. It logs in over SSH and installs everything — Python, the Lookout programs, the boot services, the radio hotplug handler, and radio-audio support — then starts and verifies them, and saves it all to flash so it survives a power-cycle.
6. It's done when the log says the router is now The Lookout and three services are running. Plug in the radio and open **`http://192.168.8.1:8080/`** in any browser. (To hear the radio in the browser, add a USB sound card, patch the radio's audio into it, and tap **🔊 Listen** on the map.)

The admin password is used once, over SSH, to log in to your own router. It is not stored or sent anywhere else.

## Name units

1. Go to the **Name units** tab. Enter the router **IP** and the **Token** (default `lookout`).
2. Click **Load from router** to pull the current unit‑ID → name table.
3. Edit the **Unit ID** / **Name** rows — for example `9076801` → `Jax 24`. **+ Add unit** adds a row; the **–** button removes one.
4. Click **Save to router**. The names appear on the map within a few seconds.

## What you need

- A **GL‑MT6000** travel router (or another OpenWrt router) — the box Lookout Manager sets up.
- A **GPS‑telemetry radio** (for example a BK M150 P25 base) plugged into the router, for live units.
- **Windows** with Python — the launcher installs Python and `paramiko` for you.

## If something goes wrong

- **Can't connect / the log stalls at login** — check the router IP and admin password, and make sure your PC is on the router's network and the router has internet for the one‑time install.
- **Names don't show** — confirm the **Token** matches the one on the router (default `lookout`) and that the router is running (open `http://<router>:8080/`).
- **"paramiko not found"** — let the launcher finish installing it, or run `py -m pip install paramiko` once.

---

*Part of **The Lookout** — https://github.com/Jim-dc95811/The-Lookout*
