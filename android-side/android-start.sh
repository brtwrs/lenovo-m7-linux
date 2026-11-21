#!/system/bin/sh
# Android side of camera and sound in Linux mode. Started by linux-boot.sh when /root/autostart-media
# exists in the Debian rootfs. Everything lives in $D (root only; see docs/12-camera.md and docs/13-audio.md):
#   minimediaservice, libcameraservice.so, vendor.lineage.camera.motor@1.0.so   (from the Halium 9 image)
#   libmediaplayerservice.so (stub), m7cam, m7audio                              (built from this repo)
#   camera   (optional: 0 = back, 1 = front; default 1)
#   volume   (optional: 0..15; default 8)
D=/data/adb/m7media; cd $D || exit 1     # root only (chmod 700): these binaries run as root
exec >>$D/start.log 2>&1; echo "== $(date) android-start"

# Camera: Android's cameraserver hangs in checkPermission without system_server. Halium's minimediaservice
# registers fake permission/appops/batterystats services and its own camera service.
for i in $(seq 90); do [ "$(getprop init.svc.cameraserver)" = running ] && break; sleep 1; done
stop cameraserver; stop media
magiskpolicy --live "allow mtk_hal_camera devmap_device chr_file { read write open ioctl getattr }"
sleep 1
( while true; do LD_LIBRARY_PATH=$D:/system/lib ./minimediaservice </dev/null >>$D/minimediaservice.log 2>&1; echo "$(date +%T) minimediaservice stopped"; sleep 3; done ) &
sleep 4
CAM=$(cat $D/camera 2>/dev/null || echo 1)
( while true; do ./m7cam $CAM 8093 1280 720 </dev/null >>$D/m7cam.log 2>&1; echo "$(date +%T) m7cam stopped"; sleep 3; done ) &

# Sound: set the stream volumes (they sit at -inf without system_server), then play PulseAudio's
# null-sink monitor (unix socket inside the chroot) through audioserver.
VOL=$(cat $D/volume 2>/dev/null || echo 8)
./m7audio volume $VOL
# the volume goes along: m7audio sets it again whenever it opens the speaker (audioserver restarts forget it)
( while true; do ./m7audio play /data/linux/run/m7pulse/pcm $VOL </dev/null >>$D/m7audio.log 2>&1; echo "$(date +%T) m7audio stopped"; sleep 3; done ) &
echo "started, camera $CAM"
