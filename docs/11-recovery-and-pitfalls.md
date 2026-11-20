# 11. Recovery, pitfalls and debugging

## Getting back to Android
* Press **Volume UP** during the first 20 s of a Linux boot → one Android boot.
* From Debian: `touch /root/android-once && reboot`.
* Disable Linux permanently: `rm /data/adb/m7linux/linux-vast`.

## Ended up in Android unexpectedly?
Magisk's **safe mode** (Volume DOWN during boot, easy to hit with a hard reset) disables all modules. Open the
Magisk app → Modules → switch `m7linux` on → reboot via the power menu. Or with adb: `su -c rm /data/adb/modules/m7linux/disable`.

## Black screen
* Panel black with backlight on after a blank (X screensaver): `start vendor.hwcomposer-2-1; sleep 4; stop vendor.hwcomposer-2-1`,
  then `echo 0 > /sys/class/graphics/fb0/blank`.
* Partly black screen with the GPU stack: you are missing one of the damage/buffer-age patches (chapter 7/8).

## Crashes and logs
* After a kernel crash the tablet reboots by itself (`panic=1`). The previous kernel log is in **`/proc/last_kmsg`**.
* Things that crash the kernel: ALSA mmap playback (any audio player), `rmmod` of the wmt (wifi) modules,
  `FBIOPUT_VSCREENINFO` with another pixel format.
* Boot log of the module: `/data/adb/m7linux/m7linux.log`.

## Small things that cost time
* `pgrep -f`/`pkill -f` over ssh also match your own ssh command line; use `pkill -x`.
* QML/JS property and function names must not start with a capital letter, and `x` is reserved.
* An OpacityMask/ShaderEffectSource of an *invisible* item does not render its children; use `layer.effect` or `hideSource`.
* When the tablet has been unplugged in BROM/fastboot, the PC sees a new USB device each time; re-run adb/mtkclient.
