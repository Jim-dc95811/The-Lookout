# Running The Lookout on an OpenWrt router (procd boot services)

The Lookout runs on a travel router (e.g. GL-MT6000) just as well as a Pi — the router
is a purpose-built, always-on network appliance, so it fits a continuous-duty job better.

These two files make the bridge and the KML server start **on their own at power-on**,
using OpenWrt's `procd` init system (the router's equivalent of the Pi's systemd units).

## One-time setup on the router (SSH in as root)

```sh
# 1. Python + the two scripts (if not already there)
opkg update && opkg install python3
cd /root
wget https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/main/bk_bridge.py
wget https://raw.githubusercontent.com/Jim-dc95811/The-Lookout/main/units_kml.py

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
  then runs `bk_bridge.py` (auto-restarts via `respawn`).
- `units-kml` starts just after and runs `units_kml.py`.
- Watch them: `logread -e bk_bridge` / `logread -e units`. Control: `/etc/init.d/<name> start|stop|restart`.
