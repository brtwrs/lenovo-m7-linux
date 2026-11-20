#!/bin/sh
# Build Droidian's wlroots (with the Android hwcomposer backend) and cage into /opt/wlr, with the M7 patches.
set -e
apt-get install -y --no-install-recommends git meson ninja-build pkg-config libwayland-dev wayland-protocols libpixman-1-dev \
  libxkbcommon-dev libinput-dev libdrm-dev libgbm-dev libegl-dev libgles-dev libudev-dev libseat-dev hwdata
. /opt/hybris/env.sh
cd /root/src
[ -d wlroots ] || git clone -b bookworm https://github.com/droidian/wlroots.git
cd wlroots && git checkout 599e4aa && git apply /root/m7-linux/patches/wlroots.diff
PKG_CONFIG_PATH=/opt/hybris/lib/pkgconfig meson setup build --prefix=/opt/wlr -Dexamples=false -Dxwayland=disabled -Dx11-backend=disabled
ninja -C build install
cd /root/src
[ -d cage ] || git clone https://github.com/cage-kiosk/cage.git
cd cage && git checkout aa91af3 && git apply /root/m7-linux/patches/cage.diff
PKG_CONFIG_PATH=/opt/wlr/lib/arm-linux-gnueabihf/pkgconfig meson setup build --prefix=/opt/wlr -Dxwayland=false
ninja -C build install
