# 10. Hardware details and what is left to do

| Part | Kernel interface | State |
|---|---|---|
| Panel | `/dev/graphics/fb0` (mtkfb), hwcomposer 2.1 | ✅ |
| Backlight | `/sys/class/leds/lcd-backlight/brightness` (0–255) | ✅ |
| GPU | `/dev/mali`, `/vendor/lib/egl/libGLES_mali.so` | ✅ via libhybris |
| Touch | `mtk-tpd`, `event2` (FocalTech) | ✅ |
| Keys | `mtk-kpd`, `event1`: KEY_VOLUMEDOWN, KEY_VOLUMEUP, KEY_POWER | 🟡 readable, not used yet |
| Headset detect | `ACCDET` input device | 🟡 |
| Wifi | `/dev/wmtWifi`, `wlan0` (nl80211) | ✅ |
| Bluetooth | `/dev/stpbt` | 🟡 untried; Android's HAL speaks raw HCI over it |
| GPS, FM | `/dev/stpgps`, `/dev/fm` | 🟡 untried |
| Accelerometer | MC34XX on I2C, `/sys/class/sensor/m_acc_misc` | 🟡 MediaTek sensor framework, not wired up |
| Light / proximity | `als_ps` framework only | 🔴 no chip on this tablet |
| LEDs | `/sys/class/leds/red`, `/sys/class/leds/green` | 🟡 sysfs |
| Vibrator | `/sys/class/leds/vibrator` | 🟡 sysfs |
| Battery / charger | `/sys/class/power_supply/battery`, charger bq2560x | ✅ readable |
| Thermal | `/sys/class/thermal/thermal_zone*` (CPU, battery, PMIC, wifi …) | ✅ |
| CPU | `cpufreq` `interactive`, 1.3 GHz | ✅ |
| Suspend / screen off | `/sys/power/state` (freeze, mem), `fb0/blank` | 🟡 untested with the GPU stack |
| Audio | `mt-snd-card` (ALSA) | 🔴 **mmap playback = kernel Oops** (`snd_pcm_mmap_data_fault`) |
| Camera | Android camera HAL only | 🔴 |
| Hardware video decoder | `Vcodec` behind Android's media stack | 🔴 not used; software decoding is enough |
| USB | `musb-hdrc` (gadget) | 🟡 e.g. USB networking |

Power: with the screen on and a live video background the tablet draws ≈ 4 W, more than the charger of a cheap
USB port may deliver; use a proper 2 A charger for a wall-mounted dashboard.
