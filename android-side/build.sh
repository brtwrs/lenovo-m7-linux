#!/bin/sh
# Build the Android-side helpers with the Android NDK (r27c tested): m7cam and m7audio.
#   NDK=/path/to/android-ndk-r27c ./build.sh
# Output in ./out; copy it to /data/adb/m7media on the tablet (chmod 700) (see docs/12-camera.md).
set -e
: "${NDK:?set NDK to the Android NDK directory}"
CC="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/armv7a-linux-androideabi28-clang"
cd "$(dirname "$0")"; mkdir -p out
"$CC" -O2 -Wall -o out/m7cam m7cam/m7cam.c -lcamera2ndk -lmediandk -landroid -llog -ldl
"$CC" -O2 -Wall -o out/m7audio m7audio/m7audio.c -laaudio -llog -ldl -lm
"$CC" -shared -fPIC -nostdlib -Wl,-soname,libmediaplayerservice.so -o out/libmediaplayerservice.so minimediaservice/mediaplayerservice-stub.c
cp android-start.sh out/
ls -l out
