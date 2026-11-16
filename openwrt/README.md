# Running The Lookout on an OpenWrt router (procd boot services)

The Lookout runs on a travel router (e.g. GL-MT6000) just as well as a Pi — the router
is a purpose-built, always-on network appliance, so it fits a continuous-duty job better.

These two files make the bridge and the KML server start **on their own at power-on**,
using OpenWrt's `procd` init system (the router's equivalent of the Pi's systemd units).

## One-time setup on the router (SSH in as root)

```sh
# 1. Python, libusb (for the box's own "you are here" GPS), and the scripts
opkg update && opkg install python3 libusb-1.0-0
cd /root
for f in bk_bridge.py gps_source.py garmin_linux.py units_kml.py; do
  wget https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/main/$f
done

# 2. The boot services
cd /etc/init.d
wget https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/main/openwrt/bk-bridge
wget https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/main/openwrt/units-kml
chmod +x bk-bridge units-kml
/etc/init.d/bk-bridge enable
/etc/init.d/units-kml enable
reboot
```

After the reboot, with the radio plugged in, the router serves live units on
`http://<router-ip>:8080/units.kml` with nothing started by hand.

- `bk-bridge` waits for the radio's `usb0` to appear, gives it `10.250.46.100/24`,
  frees a Garmin GPS 18 USB from the `garmin_gps` kernel driver (so the bridge's libusb
  reader can claim it), then runs `bk_bridge.py` (auto-restarts via `respawn`). Plug a GPS
  into the hub and the box plots itself as unit `LOOKOUT`; with none, it's radio-only.
- `units-kml` starts just after and runs `units_kml.py`.
- Watch them: `logread -e bk_bridge` / `logread -e units`. Control: `/etc/init.d/<name> start|stop|restart`.
