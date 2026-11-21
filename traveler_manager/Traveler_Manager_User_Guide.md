# Traveler Manager — User Manual

> **Installing Traveler Manager — read this first**
> - **Extract All** first (right-click the download → *Extract All*), then open the extracted folder.
> - Double-click the one file: **`Start Traveler Manager.bat`**. Everything else lives under **System Files** — leave it alone.
> - Windows may warn (unknown publisher). Click **More info → Run anyway** (or, on the zip, *Properties → Unblock* first).
> - The launcher gets your PC ready: it finds Python (installs it if missing — answer **Y**, no admin needed) and installs the one library it needs (`paramiko`, for SSH).
> - Traveler Manager sets up and manages **The Lookout Traveler** — a palm-sized GL-MT3000 that reads your radio and serves a live split-screen map. You need that box (plus the radio and the Garmin GPS) for it to do anything.

A printable copy of this guide is **Traveler_Manager_User_Guide.pdf**, right next to the `.bat`.

---

## What it is

Traveler Manager is a small Windows app that stands up and maintains **The Lookout Traveler** — the man-packable, battery box that reads your P25 radio and serves the live fleet, with your own "you are here" position, to any browser. It has two tabs:

- **Set up a router** — turn a brand-new GL-MT3000 into a Traveler in one click.
- **Name units** — give your unit IDs friendly names that show on the map.

It is a fully independent product: a Traveler box carries only Traveler files, and this app shares nothing with Lookout Manager.

## Set up a router (one click)

1. **First-boot the box and update its firmware.** On the box's own page (`http://192.168.8.1`), set an admin password and confirm it has internet, then **install the firmware update it offers and let it reboot** — do this *before* anything else. Don't set up on whatever shipped in the carton. (One time only — the box never needs the firmware touched again.)
2. Connect your PC to the box (its Wi-Fi or a LAN cable). The box must have **internet** for this one-time setup.
3. Open Traveler Manager and go to the **Set up a router** tab.
4. **New box IP** — usually `192.168.8.1` (the GL-MT3000 default). **Admin password** — the box's own admin password (the one you set on its first-boot page).
5. Click **Set up this box** and watch the log. It logs in over SSH and installs everything — Python, the GPS library, the Traveler programs, the split-screen map, the two boot services and the radio hotplug handler — then starts and verifies them, and saves it all to flash so it survives a power-cycle.
6. It's done when the log says the box is now a Lookout Traveler and **two services are running**. Plug the radio relay and the Garmin into the hub, then open **`http://192.168.8.1:8080/`** in any browser — the locked split-screen map (hybrid over street, your position centered in both).

The admin password is used once, over SSH, to log in to your own box. It is not stored or sent anywhere else.

### Where the Traveler files come from

The Traveler's own programs are **bundled with this app** in a **`Traveler Files`** folder (under *System Files*). Traveler Manager streams them straight to the box over SSH — so the install does **not** depend on GitHub or anything on the internet except the box's own package feed. Use **Change…** on the Set up tab only if you moved that folder (for example a copy from a backup). If a file is missing, the setup stops and tells you which one, before it touches the box.

The box still needs **internet once** for the two system packages (Python and the USB-GPS library, `libusb`) — those come from the box maker's own package feed. After that, the Traveler runs fully offline.

## Name units (friendly names)

1. Enter the box IP (`192.168.8.1`) and click **Load from box** — it reads the current ID→name list.
2. Edit a name, **+ Add unit** for a new one, or **-** to remove one.
3. Click **Save to box**. The names appear on the map within a few seconds. No restart.

## What makes the Traveler different from the fixed Lookout

| | The Lookout | The Lookout Traveler |
|---|---|---|
| Box | GL-MT6000 (vehicle/mains) | GL-MT3000 (battery, man-pack) |
| GPS ("you are here") | Garmin GPS 18 USB | Garmin GPS 18 USB (same) |
| Audio | Radio audio in the browser | None — you wear the radio |
| Map | Single map + Maps menu | Locked split-screen (hybrid top / street bottom), no menu |
| Services on the box | 3 (map, radio bridge, audio) | 2 (map, radio bridge) |

The radio bridge, GPS, and map-serving are the **same proven code** as the Lookout. Only the differences above are changed.

## Starting a box over (fresh start)

To wipe a box and set it up clean: on the box's page do a **factory reset**, run the GL first-boot (set the admin password again), update firmware, then run **Set up this box** here. The setup is idempotent — running it on a clean box gives a clean Traveler.

## Troubleshooting

- **"Could not log in"** — check the IP, that it's a fresh GL-MT3000, and the admin password. After a factory reset or firmware flash the box's SSH identity changes; that only affects a *manual* `ssh` (this app auto-accepts it).
- **`ssh` gives "REMOTE HOST IDENTIFICATION HAS CHANGED" / "Host key verification failed"** — only happens if you log into the box *by hand* with `ssh` (Traveler Manager never hits this). A factory reset or firmware flash gives the box a new identity, and your PC still remembers the old one. **Fix it once, forever:** double-click **`System Files\Fix SSH host-key (run once).bat`**. It clears the old key and tells your PC to stop checking that address, so `ssh root@192.168.8.1` connects clean through every future reset. You only ever run it once.
- **"only see 1 running service"** — a step failed; scroll the log for a download or install error (usually the box had no internet for Python/libusb), fix it, and run again.
- **Map is blank under the dot** — no maps on the box yet. Put a **matched pair** of maps (same area: a hybrid and a street `.tpkx` of the same extent) on the box's drive. A mismatched pair shows a red warning banner.
- **Radio shows "LINK DOWN"** — the radio relay isn't reachable on the box's USB. Check it's plugged into the hub and powered.
