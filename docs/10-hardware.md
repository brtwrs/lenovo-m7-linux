# 10. Hardware details and what is left to do

| Part | Kernel interface | State |
|---|---|---|
| Panel | `/dev/graphics/fb0` (mtkfb), hwcomposer 2.1 | ✅ |
| Backlight | `/sys/class/leds/lcd-backlight/brightness` (0–255) | ✅ |
| GPU | `/dev/mali`, `/vendor/lib/egl/libGLES_mali.so` | ✅ via libhybris |
| Touch | `mtk-tpd`, `event2` (FocalTech) | ✅ |
| Keys | `mtk-kpd`, `event1`: KEY_VOLUMEDOWN, KEY_VOLUMEUP, KEY_POWER | ✅ standby and brightness, events to HA ([chapter 14](14-hardware-services.md)) |
| Headset detect | `ACCDET` input device | 🟡 |
| Wifi | `/dev/wmtWifi`, `wlan0` (nl80211) | ✅ |
| Bluetooth | `/dev/stpbt` (raw H4 HCI) | ✅ BLE scanning; ESPHome Bluetooth proxy for HA ([chapter 14](14-hardware-services.md)) |
| GPS, FM | `/dev/stpgps`, `/dev/fm` | 🟡 untried |
| Accelerometer | MC34XX on I2C, `/sys/class/sensor/m_acc_misc` | 🟡 MediaTek sensor framework, not wired up |
| Light / proximity | `als_ps` framework only | 🔴 no chip on this tablet |
| LEDs | `/sys/class/leds/red`, `/sys/class/leds/green` | ✅ on, off, blink (`timer` trigger) |
| Vibrator | `/sys/class/leds/vibrator` (`duration`, `activate`) | ✅ |
| Battery / charger | `/sys/class/power_supply/battery`, charger bq2560x | ✅ readable |
| Thermal | `/sys/class/thermal/thermal_zone*` (CPU, battery, PMIC, wifi …) | ✅ |
| CPU | `cpufreq` `interactive`, 1.3 GHz | ✅ |
| Screen off | backlight 0 + grab the touchscreen | ✅ standby with tap/button to wake ([chapter 14](14-hardware-services.md)) |
| Suspend | `/sys/power/state` (freeze, mem) | 🟡 untested with the GPU stack |
| Audio (speaker, microphone) | Android's `audioserver` via AAudio | ✅ through PulseAudio ([chapter 13](13-audio.md)). Never use the ALSA card directly: **mmap = kernel Oops** (`snd_pcm_mmap_data_fault`) |
| Cameras (front, back) | Android's camera HAL via Halium's `minimediaservice` + Camera2 NDK | ✅ RTSP, 1280×720 H.264 ~15 fps ([chapter 12](12-camera.md)) |
| Hardware video encoder | `OMX.MTK.VIDEO.ENCODER.AVC` | ✅ used for the camera stream |
| Hardware video decoder | `Vcodec` behind Android's media stack | 🟡 not used; software decoding is enough |
| USB | `musb-hdrc` (gadget) | 🟡 e.g. USB networking |

Power: with the screen on and a live video background the tablet draws ≈ 4 W, more than the charger of a cheap
USB port may deliver; use a proper 2 A charger for a wall-mounted dashboard.
