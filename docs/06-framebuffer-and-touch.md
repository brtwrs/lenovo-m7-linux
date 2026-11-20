# 6. Screen and touch without the GPU (framebuffer + X11)

The simplest working screen: stop Android's hwcomposer and draw on `/dev/graphics/fb0`.

* Panel: 600×1024 visible, stride 608 px (2432 bytes), 32 bpp, byte order **R,G,B,A**, 3 buffers (virtual 608×3072).
* Turn it on: `echo 0 > /sys/class/graphics/fb0/blank`, backlight `/sys/class/leds/lcd-backlight/brightness` (0–255),
  after writing a frame: `echo 0,0 > /sys/class/graphics/fb0/pan`.
* **Never** call `FBIOPUT_VSCREENINFO` with another format: `mtkfb_check_var` asserts and the kernel reboots.

## X11
Debian's `xserver-xorg-video-fbdev` works without a VT:
```sh
xinit -- :0 -nolisten tcp -nocursor -keeptty -novtswitch -sharevts
```
with `Option "Rotate" "CW"` for landscape. Disable blanking (`xset s off; xset s noblank; xset -dpms`): after an
X blank the panel stays black with the backlight on (recover: `start vendor.hwcomposer-2-1; sleep 4; stop vendor.hwcomposer-2-1`).
Chromium in kiosk mode reaches ~57 fps on simple pages in pure software, but heavy pages (blur, big images) are slow.

## Touch
`mtk-tpd` (`event2`, 0–600 × 0–1024) and the keys `mtk-kpd` (`event1`). There is no udevd, and libinput (X and
Wayland) only uses devices udev tagged. `scripts/udev-fake.sh` writes those entries into `/run/udev/data/`.
For X with rotation use the libinput calibration matrix `0 1 0 -1 0 1 0 0 1`; for cage `-r` use `0 -1 1 1 0 0`
(set in `udev-fake.sh`).
