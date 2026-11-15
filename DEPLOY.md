# Deploy a Lookout in about 5 minutes (router)

This is the fast path: a brand-new GL.iNet **GL-MT6000** router becomes a live unit-tracking
box in a few minutes, mostly by clicking one button. **You do not need to know Linux.**

> **Doing this with an AI assistant?** Hand it this file. These steps are written to be read
> and followed by you and your assistant together — that is how it was built and proven.

## What you need

- A GL.iNet **GL-MT6000** ("Flint 2") router (~$170).
- A Windows PC connected to the router (Ethernet is simplest), and **internet reaching the router**.
- Your GPS-telemetry radio (e.g. a BK M150 base) with its USB cable.
- From this project: the **Lookout Manager** app (`lookout_manager/`) and **`Live_Units.kml`**.

## 1. First-boot the router

Power on the router. On your PC, open a browser to **`http://192.168.8.1`**. Follow the GL.iNet
welcome page and **set an admin password** — write it down, you'll use it in a moment. Finish to
the dashboard and confirm it shows an **internet connection** (it needs one for the next step).

## 2. One-click setup

Open **Lookout Manager** (double-click `Start Lookout Manager.bat`; the first run installs the one
SSH helper it needs). On the **Set up a router** tab:

1. **New router IP:** `192.168.8.1`
2. **Admin password:** the one you just set
3. Click **Set up this router**.

Watch the log. In a minute or two it ends with **"DONE — the router is now The Lookout."** The box
is provisioned, installed as boot services, and will come back on its own after any power cycle.

## 3. Plug in the radio and watch

Plug the radio into the router's **USB** port. On any viewing PC, open **`Live_Units.kml`** in
ArcGIS Earth (set the IP inside it to the router's address first). Within a few seconds your units
appear and move on their own — **nothing installed on the viewing PC.** A locked-down, no-admin PC
works the same way; it just opens the map file.

## 4. Name your units (optional)

On the **Name units** tab: **Load from router**, type friendly names next to the IDs, **Save to
router**. The names show on the map within a few seconds.

## That's the whole thing

One ~$170 router, read-only off the radio, serving every screen on the network — offline, no cloud.
Power it off and on and it comes right back. If the radio is ever unplugged, every map raises a red
**RADIO LINK DOWN** alarm within a second.

---

### If something goes wrong

- **The setup log can't log in:** check the IP, that it's a fresh GL-MT6000, and the admin password
  you set in step 1.
- **Setup fails on a download/install:** the router needs internet during setup (step 1). Confirm
  the dashboard shows a connection, then run it again.
- **Map stays empty after plugging in the radio:** unplug the radio's USB and plug it back in once —
  that re-triggers the link setup. Confirm the radio is powered and a unit is transmitting.
