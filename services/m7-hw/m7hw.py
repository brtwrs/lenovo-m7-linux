#!/usr/bin/env python3
"""m7-hw: hardware service for the Lenovo Tab M7 (TB-7305F) under Linux.

- Buttons (mtk-kpd): Power = standby on/off (long press is only reported), Vol+/Vol- = brightness (or wake).
- Standby: backlight off; the touchscreen (mtk-tpd) is grabbed, so the tap that wakes the screen
  doesn't reach the app.
- MQTT with Home Assistant discovery: screen (light), red/green LED (light with blink effects),
  vibrate button, battery/charging/power/temperatures, and an event per button press.
- Accelerometer (MC34XX via MediaTek's /dev/gsensor ioctl): orientation, tilt, and motion (picked up / knocked).
- Local HTTP on 127.0.0.1:8091 for the app: GET /status, POST /wake, POST /vibrate?ms=40.

Config: config.json next to this file (chmod 600):
  {"mqtt": {"host": "...", "port": 1883, "user": "...", "pass": "..."}, "id": "m7", "name": "Tablet M7"}
"""
import fcntl, json, math, os, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import evdev
import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))
ID = CFG.get("id", "m7")
NAME = CFG.get("name", "Tablet M7")
BASE = f"m7hw/{ID}"
LEDS = "/sys/class/leds/"
STATE_FILE = os.path.join(HERE, "state.json")


def read(path, default=None):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def write(path, value):
    try:
        with open(path, "w") as f:
            f.write(str(value))
    except OSError as e:
        print("write", path, e, flush=True)


class Hw:
    def __init__(self):
        try:
            s = json.load(open(STATE_FILE))
        except (OSError, ValueError):
            s = {}
        self.brightness = int(s.get("brightness", 160))   # brightness while the screen is on
        self.standby = bool(s.get("standby", False))       # persisted, so a service restart doesn't turn the screen on
        self.leds = {"red": {"on": False, "effect": None}, "green": {"on": False, "effect": None}}
        self.lock = threading.Lock()
        self.mq = None
        self.touch = None
        self.touch_grabbed = False
        self.wake_tap = False                              # after waking up: swallow the rest of this tap
        self.acc_state = {}                                # last orientation/tilt/motion, re-sent on (re)connect

    # ---------- screen ----------
    def save(self):
        try:
            json.dump({"brightness": self.brightness, "standby": self.standby}, open(STATE_FILE, "w"))
        except OSError:
            pass

    def set_screen(self, on, brightness=None, source=""):
        with self.lock:
            if brightness is not None:
                self.brightness = max(5, min(255, int(brightness)))
            self.standby = not on
            self.save()
            write(LEDS + "lcd-backlight/brightness", self.brightness if on else 0)
            self.grab_touch(not on)
        print(f"screen {'on' if on else 'standby'} brightness={self.brightness} ({source})", flush=True)
        self.report_screen()

    def grab_touch(self, grab):
        if not self.touch or grab == self.touch_grabbed:
            return
        try:
            (self.touch.grab if grab else self.touch.ungrab)()
            self.touch_grabbed = grab
        except OSError as e:
            print("grab", e, flush=True)

    # ---------- LEDs and vibrator ----------
    def set_led(self, colour, on, effect=None):
        d = LEDS + colour + "/"
        if not on:
            write(d + "trigger", "none"); write(d + "brightness", 0)
        elif effect in ("blink", "fast"):
            write(d + "trigger", "timer")
            t = 500 if effect == "blink" else 150
            write(d + "delay_on", t); write(d + "delay_off", t)
        else:
            write(d + "trigger", "none"); write(d + "brightness", 255)
        self.leds[colour] = {"on": on, "effect": effect if on else None}
        self.publish(f"led_{colour}", {"state": "ON" if on else "OFF", "effect": effect or "solid"})

    def vibrate(self, ms=60):
        ms = max(10, min(2000, int(ms)))
        write(LEDS + "vibrator/duration", ms)
        write(LEDS + "vibrator/activate", 1)

    # ---------- MQTT ----------
    def publish(self, topic, value, retain=True):
        if topic in ("orientation", "tilt", "motion"):
            self.acc_state[topic] = value
        if self.mq:
            self.mq.publish(f"{BASE}/{topic}", value if isinstance(value, str) else json.dumps(value), retain=retain)

    def report_screen(self):
        self.publish("screen", {"state": "OFF" if self.standby else "ON", "brightness": self.brightness})

    def discovery(self):
        dev = {"identifiers": [ID], "name": NAME, "model": "Lenovo Tab M7 (TB-7305F)", "manufacturer": "Lenovo", "sw_version": "m7-hw 1"}
        avail = {"availability_topic": f"{BASE}/status"}

        def cfg(comp, obj, extra):
            c = {"unique_id": f"{ID}_{obj}", "object_id": f"{ID}_{obj}", "device": dev, **avail, **extra}
            self.mq.publish(f"homeassistant/{comp}/{ID}/{obj}/config", json.dumps(c), retain=True)

        cfg("light", "screen", {"name": "Screen", "schema": "json", "state_topic": f"{BASE}/screen",
            "command_topic": f"{BASE}/screen/set", "brightness": True, "brightness_scale": 255, "icon": "mdi:tablet"})
        for colour in ("red", "green"):
            cfg("light", f"led_{colour}", {"name": f"LED {colour}", "schema": "json", "state_topic": f"{BASE}/led_{colour}",
                "command_topic": f"{BASE}/led_{colour}/set", "effect": True, "effect_list": ["solid", "blink", "fast"], "icon": "mdi:led-on"})
        cfg("button", "vibrate", {"name": "Vibrate", "command_topic": f"{BASE}/vibrate/press", "icon": "mdi:vibrate"})
        cfg("event", "button", {"name": "Button", "state_topic": f"{BASE}/button",
            "event_types": ["power", "power_long", "volume_up", "volume_down"], "icon": "mdi:gesture-tap-button"})
        cfg("sensor", "battery", {"name": "Battery", "state_topic": f"{BASE}/battery", "value_template": "{{ value_json.percent }}",
            "unit_of_measurement": "%", "device_class": "battery", "state_class": "measurement"})
        cfg("sensor", "battery_power", {"name": "Battery charge power", "state_topic": f"{BASE}/battery", "value_template": "{{ value_json.watt }}",
            "unit_of_measurement": "W", "device_class": "power", "state_class": "measurement"})
        cfg("sensor", "battery_temp", {"name": "Battery temperature", "state_topic": f"{BASE}/battery", "value_template": "{{ value_json.temp }}",
            "unit_of_measurement": "°C", "device_class": "temperature", "state_class": "measurement", "entity_category": "diagnostic"})
        cfg("sensor", "cpu_temp", {"name": "CPU temperature", "state_topic": f"{BASE}/battery", "value_template": "{{ value_json.cpu }}",
            "unit_of_measurement": "°C", "device_class": "temperature", "state_class": "measurement", "entity_category": "diagnostic"})
        cfg("sensor", "orientation", {"name": "Orientation", "state_topic": f"{BASE}/orientation", "device_class": "enum",
            "options": ["portrait", "portrait_upside_down", "landscape_left", "landscape_right", "flat_screen_up", "flat_screen_down"],
            "icon": "mdi:phone-rotate-landscape"})
        cfg("sensor", "tilt", {"name": "Tilt", "state_topic": f"{BASE}/tilt", "unit_of_measurement": "°",
            "state_class": "measurement", "icon": "mdi:angle-acute", "entity_category": "diagnostic"})
        cfg("binary_sensor", "motion", {"name": "Motion", "state_topic": f"{BASE}/motion", "device_class": "moving"})
        cfg("binary_sensor", "charging", {"name": "Charging", "state_topic": f"{BASE}/battery",
            "value_template": "{{ 'ON' if value_json.charging else 'OFF' }}", "device_class": "battery_charging"})

    def on_connect(self, c, u, f, rc, props=None):
        print("mqtt connected", rc, flush=True)
        c.publish(f"{BASE}/status", "online", retain=True)
        self.discovery()
        for t in ("screen/set", "led_red/set", "led_green/set", "vibrate/press"):
            c.subscribe(f"{BASE}/{t}")
        self.report_screen()
        for colour, s in self.leds.items():
            self.publish(f"led_{colour}", {"state": "ON" if s["on"] else "OFF", "effect": s["effect"] or "solid"})
        self.report_battery()
        for k, v in list(self.acc_state.items()):
            self.publish(k, v)

    def on_message(self, c, u, m):
        t = m.topic[len(BASE) + 1:]
        try:
            p = json.loads(m.payload or b"{}")
        except ValueError:
            p = {"state": m.payload.decode(errors="ignore")}
        if t == "screen/set":
            self.set_screen(p.get("state", "ON") == "ON", p.get("brightness"), "ha")
        elif t in ("led_red/set", "led_green/set"):
            colour = t.split("/")[0][4:]
            effect = p.get("effect", self.leds[colour]["effect"])
            self.set_led(colour, p.get("state", "ON") == "ON", None if effect == "solid" else effect)
        elif t == "vibrate/press":
            self.vibrate(200)

    def start_mqtt(self):
        m = CFG["mqtt"]
        c = mqtt.Client(client_id=f"m7hw-{ID}")
        c.username_pw_set(m["user"], m["pass"])
        c.will_set(f"{BASE}/status", "offline", retain=True)
        c.on_connect = self.on_connect
        c.on_message = self.on_message
        c.reconnect_delay_set(2, 60)
        c.connect_async(m["host"], int(m.get("port", 1883)), 60)
        c.loop_start()
        self.mq = c

    # ---------- battery and temperature ----------
    def report_battery(self):
        b = "/sys/class/power_supply/battery/"
        try:
            i = float(read(b + "current_now", 0)) / 1e6; u = float(read(b + "voltage_now", 0)) / 1e6
        except ValueError:
            i = u = 0
        cpu = None
        for z in os.listdir("/sys/class/thermal"):
            if read(f"/sys/class/thermal/{z}/type") == "mtktscpu":
                cpu = round(int(read(f"/sys/class/thermal/{z}/temp", 0)) / 1000, 1)
        # positive current_now = discharging on this kernel, so the charge power is -I·U
        self.publish("battery", {"percent": int(read(b + "capacity", 0)), "charging": read(b + "status") in ("Charging", "Full"),
                                 "watt": round(-i * u, 2), "temp": round(int(read(b + "temp", 0)) / 10, 1), "cpu": cpu})

    def battery_loop(self):
        while True:
            self.report_battery()
            time.sleep(60)

    # ---------- accelerometer ----------
    # MediaTek hwmsensor: ioctl GSENSOR_IOCTL_READ_SENSORDATA = _IOR(0x85, 0x03, int) returns "x y z" as hex text
    # (signed 32-bit) in mm/s². Axes: z out of the screen, y along the long side (portrait = natural orientation).
    ACC_REQ = (2 << 30) | (4 << 16) | (0x85 << 8) | 0x03

    def acc_read(self, fd):
        b = bytearray(64); fcntl.ioctl(fd, self.ACC_REQ, b, True)
        return [(lambda v: v - (1 << 32) if v & 0x80000000 else v)(int(w, 16)) for w in bytes(b).split(b"\0")[0].split()][:3]

    @staticmethod
    def orientation(x, y, z):
        ax, ay, az = abs(x), abs(y), abs(z)
        if az > 0.8 * 9807: return "flat_screen_up" if z > 0 else "flat_screen_down"
        if ay >= ax: return "portrait" if y > 0 else "portrait_upside_down"
        return "landscape_left" if x > 0 else "landscape_right"

    def acc_loop(self):
        fd = os.open("/dev/gsensor", os.O_RDONLY)
        avg = None; current = None; tilt_sent = None; motion_until = 0; moving = False; last = 0; failed = False
        while True:
            try:
                x, y, z = self.acc_read(fd)
            except (OSError, ValueError) as e:
                if not failed: print("acc:", repr(e), flush=True); failed = True
                time.sleep(1); continue
            if avg is None:
                avg = [x, y, z]; self.publish("motion", "OFF")
            # knock or pick-up: deviation from the running average (low-pass, ~1 s) above 1.2 m/s²
            dev = math.sqrt(sum((a - g) ** 2 for a, g in zip((x, y, z), avg)))
            avg = [g + (a - g) * 0.05 for a, g in zip((x, y, z), avg)]
            now = time.time()
            if dev > 1200: motion_until = now + 5
            if (now < motion_until) != moving:
                moving = now < motion_until
                self.publish("motion", "ON" if moving else "OFF")
            gx, gy, gz = avg
            o = self.orientation(gx, gy, gz)
            tilt = round(math.degrees(math.acos(max(-1, min(1, gz / max(1, math.sqrt(gx * gx + gy * gy + gz * gz)))))))
            if o != current and not moving:
                current = o; self.publish("orientation", o)
            if tilt_sent is None or (abs(tilt - tilt_sent) >= 3 and not moving) or now - last > 300:
                tilt_sent = tilt; last = now; self.publish("tilt", str(tilt))
            time.sleep(0.05)

    # ---------- buttons and touch ----------
    def button_event(self, kind):
        print(time.strftime("%H:%M:%S"), "button:", kind, flush=True)
        self.publish("button", {"event_type": kind}, retain=False)

    def button_loop(self):
        kpd = next(evdev.InputDevice(p) for p in evdev.list_devices() if evdev.InputDevice(p).name == "mtk-kpd")
        down = {}
        for e in kpd.read_loop():
            if e.type != evdev.ecodes.EV_KEY:
                continue
            if e.value == 1:
                down[e.code] = time.time()
                if e.code == evdev.ecodes.KEY_VOLUMEUP:
                    self.button_event("volume_up")
                    self.set_screen(True, None if self.standby else self.brightness + 25, "vol+")
                elif e.code == evdev.ecodes.KEY_VOLUMEDOWN:
                    self.button_event("volume_down")
                    self.set_screen(True, None if self.standby else self.brightness - 25, "vol-")
            elif e.value == 0 and e.code == evdev.ecodes.KEY_POWER:
                if time.time() - down.get(e.code, time.time()) > 1.5:
                    self.button_event("power_long")
                else:
                    self.button_event("power")
                    self.set_screen(self.standby, None, "power button")

    def touch_loop(self):
        self.touch = next(evdev.InputDevice(p) for p in evdev.list_devices() if evdev.InputDevice(p).name == "mtk-tpd")
        if self.standby:
            self.grab_touch(True)
        for e in self.touch.read_loop():
            if e.type == evdev.ecodes.EV_KEY and e.code == evdev.ecodes.BTN_TOUCH:
                if e.value == 1 and self.standby:
                    # wake up; the touch stays grabbed until the finger lifts, then goes back to the app
                    self.wake_tap = True
                    with self.lock:
                        self.standby = False
                        write(LEDS + "lcd-backlight/brightness", self.brightness)
                    self.report_screen()
                    print(time.strftime("%H:%M:%S"), "screen on (tap)", flush=True)
                elif e.value == 0 and self.wake_tap:
                    self.wake_tap = False
                    with self.lock:
                        self.grab_touch(False)

    # ---------- local HTTP for the app ----------
    def http(self):
        hw = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def reply(self, d):
                b = json.dumps(d).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

            def do_GET(self):
                if urlparse(self.path).path == "/status":
                    self.reply({"standby": hw.standby, "brightness": hw.brightness})
                else:
                    self.send_error(404)

            def do_POST(self):
                u = urlparse(self.path); q = parse_qs(u.query)
                if u.path == "/wake":
                    if hw.standby:
                        hw.set_screen(True, None, "app")
                    self.reply({"ok": True})
                elif u.path == "/vibrate":
                    hw.vibrate(q.get("ms", ["40"])[0]); self.reply({"ok": True})
                else:
                    self.send_error(404)

        ThreadingHTTPServer(("127.0.0.1", 8091), H).serve_forever()


def main():
    hw = Hw()
    write(LEDS + "lcd-backlight/brightness", 0 if hw.standby else hw.brightness)
    hw.start_mqtt()
    for target in (hw.button_loop, hw.touch_loop, hw.battery_loop, hw.acc_loop):
        threading.Thread(target=target, daemon=True).start()
    print("m7-hw started", flush=True)
    hw.http()


if __name__ == "__main__":
    main()
