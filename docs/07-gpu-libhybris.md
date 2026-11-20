# 7. GPU: libhybris + Halium bionic

The only GPU driver is Android's proprietary Mali blob (`/vendor/lib/egl/libGLES_mali.so`), linked against
Android's libc (bionic). [libhybris](https://github.com/libhybris/libhybris) loads such Android libraries into a
glibc process.

## The bionic problem
With the tablet's own bionic every libhybris program segfaults immediately: bionic reads TLS slot 1, which glibc
uses for something else. Halium solves this with a **patched bionic**. We borrow it from LuneOS' Halium 9 image
for the Nexus 4 (mako, also armv7): `scripts/fetch-halium.sh` downloads it and extracts `libc.so`, `libm.so`,
`libdl.so` and `libhwc2_compat_layer.so` (the latter is needed for the compositor, chapter 8).

## Build
In Debian on the tablet (copy this repo to `/root/m7-linux` and run `fetch-halium.sh` first, then put
`halium-libs/` in `/root/m7-linux/`):
```sh
sh /root/m7-linux/scripts/build-libhybris.sh
```
This builds libhybris `7079712` with `patches/libhybris.diff`, configured with `--enable-arch=arm
--enable-mali-quirks --enable-wayland` and Halium's Android 9 headers, into `/opt/hybris`, and installs
`/opt/hybris/env.sh`:
```sh
LD_LIBRARY_PATH=/opt/hybris/lib
HYBRIS_LD_LIBRARY_PATH=/opt/hybris/android/lib:/vendor/lib/egl:/vendor/lib/hw:/vendor/lib:/system/lib
```
The Halium bionic comes first in `HYBRIS_LD_LIBRARY_PATH`, so it wins over the tablet's own.

## Check
```sh
. /opt/hybris/env.sh; /opt/hybris/bin/test_egl_configs     # should load Mali: EGL 1.4, ~28 configs
```

## The two libhybris patches
* **Buffer age 0** instead of the hard-coded "2 // sure :)": with rotating Wayland buffers the age was wrong,
  apps only redrew the changed part on a stale buffer, and parts of the screen turned black.
* `waylandws_createWlBuffer`: an image may come from another (server) display; then use the caller's client
  display, which knows `android_wlegl` (otherwise WPE segfaults).
