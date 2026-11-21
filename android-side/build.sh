#!/bin/sh
# Build the Android-side helpers with the Android NDK (r27c tested): m7cam and m7audio.
#   NDK=/path/to/android-ndk-r27c ./build.sh
# Output in ./out; copy it to /data/adb/m7media on the tablet (chmod 700) (see docs/12-camera.md).
set -e
: "${NDK:?set NDK to the Android NDK directory}"
# ARCH=arm (Android 9, M7; default) or ARCH=arm64 (M8 and newer)
case "${ARCH:-arm}" in
  arm)   TRIPLE=armv7a-linux-androideabi28 ;;
  arm64) TRIPLE=aarch64-linux-android31 ;;
  *) echo "ARCH must be arm or arm64" >&2; exit 1 ;;
esac
CC="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/$TRIPLE-clang"
CXX="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/$TRIPLE-clang++"
cd "$(dirname "$0")"; mkdir -p out
"$CXX" -O2 -Wall -c -o out/binderpool.o common/binderpool.cpp
"$CC" -O2 -Wall -c -o out/m7cam.o m7cam/m7cam.c && "$CXX" -static-libstdc++ -o out/m7cam out/m7cam.o out/binderpool.o -lcamera2ndk -lmediandk -landroid -llog -ldl
"$CC" -O2 -Wall -c -o out/m7audio.o m7audio/m7audio.c && "$CXX" -static-libstdc++ -o out/m7audio out/m7audio.o out/binderpool.o -laaudio -llog -ldl -lm
rm -f out/*.o
"$CC" -O2 -Wall -o out/fakeperm common/fakeperm.c -lbinder_ndk -ldl
"$CC" -shared -fPIC -nostdlib -Wl,-soname,libmediaplayerservice.so -o out/libmediaplayerservice.so minimediaservice/mediaplayerservice-stub.c
cp android-start.sh out/
ls -l out
