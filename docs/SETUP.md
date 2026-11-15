# Building The Lookout — step by step

This walks you from a blank Raspberry Pi to a self-running GPS coordinate server that feeds your whole network. No prior Linux experience assumed — every command is spelled out, with what a good result looks like.

**What you'll end up with:** plug the radio into the Pi, power it on, and the Pi serves live positions to every ArcGIS Earth and phone on your LAN — on its own, no login, forever.

---

## Step 1 — Put Raspberry Pi OS on the card, with SSH on

1. Download the **Raspberry Pi Imager** from [raspberrypi.com/software](https://www.raspberrypi.com/software/) and flash **Raspberry Pi OS** to a microSD card.
2. In the Imager's settings (the gear / "Edit settings"), set a **username and password** and **enable SSH** — that lets you drive the Pi from your PC with no monitor or keyboard.
   - No settings screen? After flashing, open the card's `bootfs` drive on your PC and create an empty file literally named `ssh` (no extension). That turns SSH on at first boot.
3. Put the card in the Pi, connect it to your network (ethernet is simplest), and power it on.

## Step 2 — Find the Pi on your network

The Pi gets an address from your router. Easiest way to find it: log into your **router's admin page** and look at its list of connected devices / DHCP leases — the Pi shows up by its hostname. Note its IP (for example `192.168.2.38`).

> Windows' `ping <hostname>.local` is unreliable; the router's device list is the sure way.

From a **Command Prompt on your PC**, connect:

```
ssh <username>@<pi-ip>
```

Enter the password you set. A green `username@hostname:~ $` prompt means you're in.

## Step 3 — Plug in the radio, confirm the USB link

Plug the GPS-telemetry radio into one of the Pi's USB ports. The radio presents itself as a USB network adapter, and the Pi loads the driver automatically — no install. Check it appeared:

```
ip addr show usb0
```

Good result: a line with **`usb0`** and `state UP`. (If you see `rndis_host` / `cdc_ether` scroll by in `dmesg`, that's the driver attaching — exactly right.)

## Step 4 — Give the link an address and test the radio

The radio sits on its own little subnet. Give the Pi an address on it (match this to your radio — the default here is for a radio at `10.250.46.6`):

```
sudo ip addr add 10.250.46.100/24 dev usb0
```

Confirm you can reach the radio:

```
ping -c 4 10.250.46.6
```

Good result: **`0% packet loss`**. That means the Pi and the radio are talking.

(Optional) prove the radio answers the subscribe handshake:

```
python3 -c "import socket; s=socket.create_connection(('10.250.46.6',65535),timeout=5); s.sendall(bytes([0x80,0x04,0x18,0xe4,0x81])); s.settimeout(12); print(s.recv(8192).hex(' '))"
```

A short reply beginning `80 04 19 ...` is the radio acknowledging — you're ready.

## Step 5 — Copy the bridge over and test-run it

From your **PC's Command Prompt** (not the Pi window), copy the program up:

```
scp bk_bridge.py <username>@<pi-ip>:~
```

Back in the **Pi window**, run it:

```
python3 bk_bridge.py
```

Good result — it reports, in order:

```
[bridge] serving NMEA on tcp 0.0.0.0:10110 - connect any device here
[radio] connected + subscribed - listening for GPS
[radio] alive - subscribed and waiting (no units transmitting yet)
```

That heartbeat **is** success: the bridge is holding the radio and serving the network, just waiting for a unit to key up. Press **Ctrl+C** to stop the test — the next step runs it properly.

## Step 6 — Install it as a boot service

So it starts itself forever. Copy the service file up (same as Step 5) or create it on the Pi, then:

```
sudo cp bk-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bk-bridge
systemctl status bk-bridge --no-pager
```

Good result: **`enabled`** and **`active (running)`**.

> The service file assumes the program is at `/home/pi/bk_bridge.py` and brings `usb0` up to `10.250.46.100/24` before starting. If your username isn't `pi` or your radio uses a different subnet, edit those two lines in `bk-bridge.service` to match.

## Step 7 — Verify it reached the radio

"Running" only means the program started; confirm it actually connected:

```
journalctl -u bk-bridge -n 15 --no-pager
```

Good result: you see **`[radio] connected + subscribed`** and steady `alive` heartbeats — now owned by the service, not you.

**Done.** From here on, plug the radio into the Pi, power on, and it serves the feed by itself.

---

## Using the feed

- **Watch it live, anytime:** `journalctl -u bk-bridge -f` (Ctrl+C stops *watching*, not the service).
- **Any device reads it** at **`<pi-ip>:10110`** — a phone/tablet NMEA app, a chart plotter, or a Windows tracker.
- **ArcGIS Earth** opens the Pi's `units.kml` as a NetworkLink and pulls it on a timer — no install on the PC (see the next section).
- **Control the service:** `sudo systemctl restart|stop|status bk-bridge`.

---

## The live units layer in ArcGIS Earth

`bk_bridge.py` puts clean NMEA on the network. `units_kml.py` turns that into a moving map layer: it reads the bridge's feed, tracks the latest position per unit, and serves a live `units.kml` on port **8080** that any ArcGIS Earth pulls on a timer.

**1. Copy it to the Pi** (from your PC's Command Prompt):

```
scp units_kml.py <username>@<pi-ip>:~
```

**2. See it work right now — no field unit needed.** On the Pi:

```
python3 units_kml.py --demo
```

That serves three synthetic units walking in circles. On a viewing PC, open **`Live_Units.kml`** in ArcGIS Earth (edit `PI-IP` in that file to your Pi's address first). Within a few seconds three named units appear and crawl across the map on their own — that's the whole pipeline proven on a real screen.

**3. Run it for real.** Stop the demo (Ctrl+C) and run it plain — it now reads live positions from the bridge:

```
python3 units_kml.py
```

**4. Make it a boot service** (so it comes up with the bridge):

```
sudo cp units-kml.service /etc/systemd/system/
sudo systemctl enable --now units-kml
```

**Name your units:** drop an `aliases.json` next to `units_kml.py` mapping IDs to names, e.g. `{"7101": "Engine 7", "7102": "Tanker 2"}`. Unknown units show their raw ID.

**How refresh is set:** `Live_Units.kml` carries `<refreshInterval>3</refreshInterval>` — ArcGIS Earth re-pulls every 3 seconds. Change that number to pull faster or slower.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ssh: connection refused` | SSH not enabled — redo Step 1 (the empty `ssh` file on `bootfs`). |
| `usb0` has no address | Run the `ip addr add` from Step 4; the boot service does this for you once installed. |
| `ping` to the radio fails | Wrong subnet — match the `ip addr` and the radio's real address. |
| "Python was not found" **on Windows** | You ran a Pi command in the Windows Command Prompt. The bridge runs **on the Pi** (`python3 bk_bridge.py` in the green `username@hostname` window). The only thing that runs on Windows is the `scp` copy. |
| Bridge shows `alive ... no units transmitting` forever | Normal with no field units keying up — it's holding the radio and will show positions the instant one transmits. |

## Adapting to a different radio

The bridge doesn't care how the bytes are framed — it scans the stream for valid NMEA sentences and checksums them. To point it at a different radio, edit the constants at the top of `bk_bridge.py`:

- `RADIO_IP`, `RADIO_PORT` — where your radio's feed lives.
- `SUBSCRIBE` — the handshake bytes, if your radio needs one to start streaming (leave empty if not).

Anything that emits `$GxGGA`/`$GxRMC`-style NMEA on a TCP port will work.
