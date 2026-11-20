# 1. Overview and requirements

## Hardware
* Lenovo Tab M7, **TB-7305F** (wifi). Tested firmware: Android 9 Go, build `PPR1.180610.011`.
* SoC MediaTek MT8321 (reports itself as **MT6580**), 4× Cortex-A7 1.3 GHz, 32-bit (armhf).
* GPU Mali-400 MP (Utgard): OpenGL ES 2.0 only.
* 1 GB RAM (≈ 800 MB free under Linux), 16 GB eMMC, 1024×600 panel (portrait 600×1024).

## You need
* A Linux PC or Mac with Python 3, `adb`/`fastboot` (Android platform-tools) and [mtkclient](https://github.com/bkerler/mtkclient).
* A USB cable. Patience with the BROM button trick.
* Docker (with arm emulation, `qemu-user-static`/binfmt) to build the rootfs, or build it any other way you like.
* Your wifi name and password.

## Why not mainline / postmarketOS?
Mainline Linux supports the MT6580 only up to the serial console (no clocks, pinctrl, display, wifi). The
stock 4.9 kernel has all drivers, so this project keeps that kernel and Android's vendor userspace for the
hardware, and runs Debian next to it. The Mali-400 would work with the open `lima` driver only on a kernel
≥ 5.2 with DRM, which this kernel does not have (display is `mtkfb`/hwcomposer, no DRM).

## Order of work
1. Unlock + root (wipes the tablet). 2. Debian rootfs. 3. Boot module (Linux by default).
4. Wifi + ssh. Now you can work over ssh. 5. Then either X11 on the framebuffer (simple, software) or the
GPU stack (libhybris, wlroots, cage) for smooth apps.
