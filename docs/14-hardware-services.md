# 14. Buttons, standby, LEDs, vibrator, accelerometer and Bluetooth

Two small Python services in `services/m7-hw/` make the rest of the hardware usable, with Home Assistant in mind.

## m7hw.py: buttons, screen standby, LEDs, vibrator, accelerometer, battery

* **Power button**: screen standby on/off (backlight 0, touchscreen grabbed so the tap that wakes the screen
  doesn't reach your app). A long press (> 1.5 s) is only reported.
* **Volume up/down**: brightness ±25 (or wake the screen).
* **Tap to wake** while in standby.
* Standby and brightness survive a restart of the service (`state.json`).
* **Accelerometer**: orientation (portrait, landscape, flat, which side up), tilt in degrees, and a motion sensor
  that turns on for 5 s when the tablet is picked up or knocked (deviation from the running average above
  1.2 m/s²). Handy to notice a wall tablet being taken off the wall.
  The MC34XX has no sysfs values on this kernel; MediaTek's old ioctl on `/dev/gsensor` does work:
  `_IOR(0x85, 0x03, int)` fills a buffer with `"x y z"` as **hex** text (signed 32-bit), in mm/s².
* **MQTT with Home Assistant discovery** (device "Tablet M7"): screen as a light with brightness, red and green
  LED as lights with `solid`/`blink`/`fast` effects, a vibrate button, an event entity for button presses
  (`power`, `power_long`, `volume_up`, `volume_down`), orientation, tilt, motion, battery %, charge power, charging, battery and CPU
  temperature.
* **Local HTTP for your app** on 127.0.0.1:8091: `GET /status` (standby, brightness), `POST /wake`,
  `POST /vibrate?ms=40`. Useful to wake the screen when your app shows something important.

```sh
apt install --no-install-recommends python3-evdev python3-paho-mqtt
mkdir -p /root/m7-hw && cp services/m7-hw/m7hw.py /root/m7-hw/
umask 077; cat > /root/m7-hw/config.json <<'EOF'
{"mqtt": {"host": "192.168.1.10", "port": 1883, "user": "m7", "pass": "..."}, "id": "m7", "name": "Tablet M7"}
EOF
```

Notes:
* `current_now` is positive while **discharging** on this kernel; the reported charge power is −I·U.
* The charger input is limited to 1 A by the kernel; with a bright screen and live video the battery can still
  drain slowly on a weak USB port.
* There is no light sensor, so automatic brightness has to come from a sensor in the room.

## m7bt.py: ESPHome Bluetooth proxy

The combo chip's Bluetooth is a raw H4 HCI device at `/dev/stpbt` (no BlueZ on this kernel). `m7bt.py` scans
passively (~30 % duty cycle, because Bluetooth shares the 2.4 GHz antenna with wifi) and speaks just enough of
the ESPHome native API on port 6053 to act as a **Bluetooth proxy** in Home Assistant. It announces itself over
mDNS, so HA discovers it as an ESPHome device.

```sh
apt install --no-install-recommends python3-zeroconf
cp services/m7-hw/m7bt.py /root/m7-hw/
echo '{"name": "m7-bt", "friendly": "Tablet M7 BT", "allowed": ["<Home Assistant IP>"]}' > /root/m7-hw/bt.json
```

* The plaintext ESPHome API has no authentication. m7bt therefore only accepts connections from the addresses
  in `allowed`; without that list it refuses everything.
* The chip reports MediaTek's default address (`00:00:46:65:80:01`), the same on every tablet; m7bt derives a
  unique, locally administered address from the wifi MAC instead, because HA uses it as the proxy's ID.
* Passive scanning and raw advertisements only; no active connections.

## Starting them

From your app's start script, before the compositor:

```sh
pgrep -f m7hw.py >/dev/null || (cd /root/m7-hw && setsid python3 m7hw.py </dev/null >/tmp/m7hw.log 2>&1 &)
pgrep -f m7bt.py >/dev/null || (cd /root/m7-hw && setsid python3 m7bt.py </dev/null >/tmp/m7bt.log 2>&1 &)
```
