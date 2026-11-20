#!/bin/sh
# Fetch the Halium-patched bionic (libc/libm/libdl) and libhwc2_compat_layer.so from LuneOS' Halium 9 image for
# the Nexus 4 (mako, armv7). Stock Android bionic crashes under glibc (TLS slot conflict); Halium's does not.
# Needs: curl, python3, e2fsprogs (debugfs). Output: ./halium-libs/
set -e
U=https://github.com/webOS-ports/halium-images/releases/download/halium-luneos-9.0-20240313-1-mako.tar.bz2/halium-luneos-9.0-20240313-1-mako.tar.bz2
mkdir -p halium-tmp halium-libs; cd halium-tmp
[ -f h9.tar.bz2 ] || curl -L -o h9.tar.bz2 "$U"
tar xjf h9.tar.bz2 --wildcards '*system.img'
IMG=$(find . -name system.img | head -1)
python3 ../simg2img.py "$IMG" system.raw 2>/dev/null || cp "$IMG" system.raw
for f in libc.so libm.so libdl.so libhwc2_compat_layer.so; do
  debugfs -R "dump /system/lib/$f ../halium-libs/$f" system.raw 2>/dev/null || debugfs -R "dump /lib/$f ../halium-libs/$f" system.raw
done
ls -la ../halium-libs
