# Debian on the Lenovo Tab M7 (TB-7305F), with the GPU

Run a real Debian 12 on the cheap Lenovo Tab M7 (TB-7305F, MediaTek MT8321 / MT6580, Mali-400 MP, 1 GB RAM),
with wifi, touch and a **GPU-accelerated Wayland compositor**, so it can drive a smooth wall dashboard
(Qt Quick at 60 fps, or a WebKit kiosk), without the Android UI and its background noise.

This is not a mainline port: mainline Linux knows the MT6580 only up to a serial console. Instead, the stock
Lenovo kernel (4.9) and Android's vendor drivers keep running, and Debian runs next to them in a chroot that
takes over the screen. The GPU is used through [libhybris](https://github.com/libhybris/libhybris) and
Android's own hwcomposer, the same way Halium/Droidian phones do it.

> ⚠️ **Read [docs/02-unlock-and-root.md](docs/02-unlock-and-root.md) first.** Unlocking the bootloader **wipes
> the tablet**, and a mistake in the BROM steps can leave it unbootable until you restore your backup.
> You do this at your own risk.

## What works

| | Status | Notes |
|---|---|---|
| Screen, backlight | ✅ | via Android's hwcomposer (GPU) or plain `/dev/graphics/fb0` (X11, software) |
| **GPU** (Mali-400 MP, GLES 2) | ✅ | libhybris + Halium 9 bionic + Droidian wlroots + cage; 60 fps |
| Touch | ✅ | libinput with fake udev data |
| Wifi | ✅ | MediaTek combo chip via `/dev/wmtWifi`, Debian's `wpa_supplicant` |
| Battery, charging | ✅ | readable in `/sys/class/power_supply/battery` (%, status, current, voltage, temp) |
| Thermal sensors, cpufreq | ✅ | 10 thermal zones, `interactive` governor |
| Video decoding (H.264) | ✅ | in software with GStreamer; 720p30 live RTSP ≈ 15 % CPU |
| Buttons (Vol−, Vol+, Power) | 🟡 | present as `mtk-kpd` (`event1`), readable with evdev; Vol+ is used as boot escape |
| Accelerometer (MC34XX) | 🟡 | on I2C, MediaTek sensor framework (`m_acc_misc`); not wired up yet |
| Notification LEDs (red/green), vibrator | 🟡 | `/sys/class/leds/{red,green,vibrator}`; not wired up yet |
| Bluetooth | 🟡 | `/dev/stpbt` (same combo chip as wifi); not tried yet |
| Screen off / suspend | 🟡 | `fb0 blank`, `/sys/power/state` (freeze, mem); untested with the GPU stack |
| **Audio** | 🔴 | ALSA card exists, but **mmap playback crashes the kernel**. Never let anything play audio |
| Camera | 🔴 | only through Android's camera HAL; no `/dev/video*` |
| Light / proximity sensor | 🔴 | the framework is there, but the tablet has no such chip |

## How it fits together

```
 ┌────────────────────────── Lenovo kernel 4.9 (stock, with Magisk in recovery) ──────────────────────────┐
 │                                                                                                         │
 │  Android init (still PID 1)                 Debian 12 armhf chroot in /data/linux                       │
 │  ├─ vendor drivers + firmware (wifi, GPU)   ├─ wpa_supplicant + udhcpc   → wifi                         │
 │  ├─ vendor.hwcomposer-2-1 (HIDL)  ◄───────┐ ├─ sshd :2222                                               │
 │  └─ zygote / surfaceflinger: STOPPED      │ ├─ cage (Wayland kiosk) ── wlroots "hwcomposer" backend     │
 │                                           │ │      │                                                    │
 │  Magisk module m7linux                    └─┼── libhwc2_compat_layer (HIDL client, from Halium 9)       │
 │  └─ post-fs-data.sh → linux-boot.sh         │      │                                                    │
 │                                             │  libhybris ── Halium 9 bionic ── /vendor/lib/egl (Mali)   │
 │                                             └─ your app: Qt Quick (EGL/wayland) or WPE WebKit (cog)     │
 └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

* Android still boots its kernel, init, vendor services and drivers. Very early (Magisk `post-fs-data`), the
  `m7linux` module decides whether this boot is a Linux boot, and if so keeps the Android UI from starting.
* Debian runs as a chroot on the data partition. Nothing of Android is modified on disk, so you can still boot
  Android (press **Volume UP** during boot, see below).
* Drawing: your app uses EGL through libhybris, which loads Android's Mali driver with a Halium-patched bionic.
  cage composites with wlroots' hwcomposer backend, which hands buffers to Android's hwcomposer service.

## Getting started

1. [Overview and requirements](docs/01-overview.md)
2. [Unlock the bootloader and root (Magisk in recovery)](docs/02-unlock-and-root.md)
3. [Build and install the Debian rootfs](docs/03-debian-rootfs.md)
4. [Install the boot module: Linux by default, Android on request](docs/04-boot-module.md)
5. [Wifi](docs/05-wifi.md)
6. [Screen and touch without the GPU (framebuffer + X11)](docs/06-framebuffer-and-touch.md)
7. [GPU: libhybris + Halium bionic](docs/07-gpu-libhybris.md)
8. [Compositor: wlroots (hwcomposer backend) + cage](docs/08-compositor.md)
9. [Apps: Qt Quick (recommended), live video, WPE WebKit kiosk](docs/09-apps.md)
10. [Hardware details and what is left to do](docs/10-hardware.md)
11. [Recovery, pitfalls and debugging](docs/11-recovery-and-pitfalls.md)

## Repository layout

| Path | What |
|---|---|
| `magisk-module/m7linux/` | the boot module (`post-fs-data.sh`, `linux-boot.sh`) |
| `scripts/` | rootfs build, chroot, Halium download, build scripts, start scripts, frp tool |
| `patches/` | patches against libhybris, Droidian wlroots and cage (see [patches/README.md](patches/README.md)) |
| `examples/qt/` | `m7-launcher` (24-bit EGL + `LiveVideo` RTSP item) and a minimal QML demo |
| `docs/` | step-by-step guides |

No binaries from Lenovo, MediaTek or Halium are included. You extract or download them yourself (the scripts
show how).

## Status of this repo

Everything here runs on a real TB-7305F (Android 9 Go firmware, `PPR1.180610.011`) as a daily wall dashboard.
The build scripts were reconstructed from that working setup and documented step by step; if a step fails for
you, please open an issue with the log.

## License

The scripts, docs and example code in this repository are MIT licensed (see [LICENSE](LICENSE)). The patches in
`patches/` modify third-party projects and fall under their licenses: libhybris (Apache-2.0), wlroots (MIT),
cage (MIT).
