#!/bin/sh
# Build libhybris on the tablet (inside the Debian chroot) into /opt/hybris, with the M7 patch.
set -e
apt-get install -y --no-install-recommends git build-essential autoconf automake libtool pkg-config \
  libwayland-dev wayland-protocols libegl-dev
mkdir -p /root/src && cd /root/src
[ -d android-headers ] || git clone https://github.com/Halium/android-headers.git   # Android 9 headers
[ -d libhybris ] || git clone https://github.com/libhybris/libhybris.git
cd libhybris && git checkout 7079712 && git apply /root/m7-linux/patches/libhybris.diff
cd hybris && ./autogen.sh && ./configure --prefix=/opt/hybris --enable-arch=arm --enable-mali-quirks --enable-wayland \
  --with-android-headers=/root/src/android-headers --with-default-egl-platform=x11 \
  --with-default-hybris-ld-library-path=/vendor/lib/egl:/vendor/lib/hw:/vendor/lib:/system/lib
make -j4 && make install
mkdir -p /opt/hybris/android/lib && cp /root/m7-linux/halium-libs/*.so /opt/hybris/android/lib/
cp /root/m7-linux/scripts/hybris-env.sh /opt/hybris/env.sh
