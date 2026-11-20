# 8. Compositor: wlroots (hwcomposer backend) + cage

There is no DRM/KMS device, so normal Wayland compositors cannot drive the display. Droidian maintains a wlroots
fork with an **Android hwcomposer backend**: it talks HIDL to Android's `vendor.hwcomposer-2-1` service through
`libhwc2_compat_layer.so`. [cage](https://github.com/cage-kiosk/cage) on top gives a full-screen kiosk.

## Build
```sh
sh /root/m7-linux/scripts/build-wlroots-cage.sh     # → /opt/wlr
```
* wlroots: `droidian/wlroots`, branch `bookworm` (`599e4aa`), with `patches/wlroots.diff`.
* cage: `aa91af3` (0.1.3), with `patches/cage.diff`.

## Run
The hwcomposer service must run, and surfaceflinger must not (`linux-boot.sh` takes care of that in GPU mode).
```sh
. /opt/hybris/env.sh
export LD_LIBRARY_PATH=/opt/wlr/lib/arm-linux-gnueabihf:/opt/hybris/lib XDG_RUNTIME_DIR=/tmp/xdg
export WLR_BACKENDS=hwcomposer,libinput XDG_SEAT=seat1 EGL_PLATFORM=hwcomposer
/root/m7-linux/scripts/udev-fake.sh seat1
/opt/wlr/bin/cage -r -- <your wayland app>        # -r = rotate to landscape
```
Clients use `EGL_PLATFORM=wayland` with libhybris' Wayland EGL. Screenshots: `grim` with
`XDG_RUNTIME_DIR=/tmp/xdg WAYLAND_DISPLAY=wayland-0` (wlroots screencopy).

## What the patches fix
| Patch | Why |
|---|---|
| wlroots: 1×1 pbuffer instead of a surfaceless context, `EGL_PBUFFER_BIT` in the config | Mali-400 cannot do surfaceless |
| wlroots: no partial damage to the hwcomposer, buffer age −1, `glFinish()` before swap, damage region no-op | otherwise black/half-drawn areas: the MTK hwcomposer refreshed only the damaged part and gets no fence |
| cage: `wlr_backend_autocreate(display, NULL)`, wlroots ≥ 0.12, subsurface API | the Droidian wlroots is "0.12" with parts of the 0.13 API |
| cage: allow running as root | we run everything as root in the chroot |
| cage: no direct scan-out | the hwcomposer backend does not support it |
| cage: forward `wl_touch.frame` | Qt waits for the frame event before it delivers a touch; without it most taps were lost |
