# 4. The boot module: Linux by default, Android on request

`magisk-module/m7linux` is a tiny Magisk module. Install it by copying the folder to
`/data/adb/modules/m7linux/` (`chmod 755 *.sh`) and rebooting.

## What it does
`post-fs-data.sh` runs very early. It decides:

| File | Effect |
|---|---|
| `/data/local/tmp/linux-vast` | **always Linux** (create it once: `touch /data/local/tmp/linux-vast`) |
| `/data/local/tmp/linux-mode` | Linux for one boot (deleted at boot) |
| `/data/linux/root/android-once` | Android for one boot (deleted at boot) |
| neither | normal Android |

`linux-boot.sh` then:
1. keeps stopping `zygote`, `surfaceflinger` and the boot animation for 60 s (init restarts them otherwise);
   without the GPU stack it also stops `vendor.hwcomposer-2-1`, so the framebuffer is free;
2. turns the panel and backlight on;
3. switches on the wifi chip and starts Debian's `wpa_supplicant`, `udhcpc` and `sshd -p 2222`;
4. starts the screen stack: the Qt app (`/root/autostart-qml` + `/root/autostart-gpu`), a WPE kiosk
   (`/root/kiosk-url` + `/root/autostart-gpu`), or X11 (`/root/autostart-x`).

Log: `/data/local/tmp/m7linux.log`.

## Safety nets
* **Volume UP** during the first 20 s of a Linux boot → reboots once into Android.
* **Never use Volume DOWN during boot**: that is Magisk's *safe mode*. It disables all modules (a `disable`
  file in the module folder). To recover: Android → Magisk app → Modules → switch `m7linux` on → reboot with the
  power button (hold Power → Restart).
* If a Linux boot does not reach `sshd` within 5 minutes, the tablet reboots and the next boot is Android
  (`linux-attempt` marker). Create `/data/local/tmp/linux-stay` to disable that while debugging.
* From Debian: `touch /root/android-once && reboot` gives one Android boot.
