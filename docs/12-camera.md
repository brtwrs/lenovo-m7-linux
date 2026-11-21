# 12. Camera

Both cameras (0 = back, 1 = front) work in Linux mode, as an RTSP stream: 1280×720 H.264 from the hardware
encoder, about 15 fps, `rtsp://<tablet>:8554/camera` with basic auth. Home Assistant can use it as a Generic
Camera.

There is no `/dev/video*`: MediaTek's camera only exists behind Android's camera HAL. So the camera stays an
Android thing, and a small Android-side program hands the video to Linux.

```
Android side (bionic)                                           Linux side (Debian chroot)
minimediaservice (Halium 9) ── camera service
m7cam: Camera2 NDK ─▶ OMX.MTK H.264 encoder ──tcp 127.0.0.1:8093──▶ m7cam-rtsp.py (GstRtspServer) ─▶ :8554
```

* **On demand.** The camera only opens while something reads the stream, and closes 30 s after the last
  viewer. The encoder is created once at startup (that takes ~9 s on this SoC); the camera itself starts in
  ~0.5 s.
* `m7cam` only accepts clients that run as root, and only listens on 127.0.0.1. The RTSP server asks for a password.

## What you need

| File | Where from | To |
|---|---|---|
| `minimediaservice`, `libcameraservice.so`, `vendor.lineage.camera.motor@1.0.so` | the Halium 9 system image from [chapter 7](07-gpu-libhybris.md) (`/system/bin`, `/system/lib`) | `/data/adb/m7media/` |
| `libmediaplayerservice.so` (stub), `m7cam`, `m7audio`, `android-start.sh` | `android-side/build.sh` (Android NDK) | `/data/adb/m7media/` |
| `m7cam-rtsp.py`, `cam.json` | `services/m7-cam/` | `/root/m7-cam/` in Debian |

```sh
# on your PC
NDK=/path/to/android-ndk-r27c android-side/build.sh
debugfs -R "dump /system/bin/minimediaservice minimediaservice" system.raw     # same for the two .so files
# on the tablet (as root, Android side)
mkdir -p /data/adb/m7media && chmod 700 /data/adb/m7media     # copy the files in, chmod 755 the binaries
# in Debian
apt install --no-install-recommends gir1.2-gst-rtsp-server-1.0 python3-gi gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
umask 077; echo '{"user": "m7", "password": "<something long>", "port": 8554}' > /root/m7-cam/cam.json
touch /root/autostart-media          # linux-boot.sh then starts android-start.sh
```

Start `m7cam-rtsp.py` from your app's start script (e.g. next to the compositor in `qt-start.sh`):

```sh
pgrep -f m7cam-rtsp.py >/dev/null || (cd /root/m7-cam && setsid python3 m7cam-rtsp.py </dev/null >/tmp/m7cam-rtsp.log 2>&1 &)
```

The camera id is in `/data/adb/m7media/camera` (default 1, the front camera, which faces the room on a wall).

## Pitfalls, in the order you hit them

1. **Android's `cameraserver` hangs** in `checkPermission`: there is no system_server in Linux mode, so nobody
   answers. Halium's `minimediaservice` registers fake `permission`, `appops` and `batterystats` services and
   runs its own camera service. `android-start.sh` stops `cameraserver` and `media` first.
2. `minimediaservice` also wants `MediaPlayerService`; the mako library from the Halium image doesn't link on
   this device. It only calls `MediaPlayerService::instantiate()`, so an empty stub library is enough.
3. **SELinux** keeps the camera HAL from opening `/dev/devmap`, so the sensor never powers on:
   `magiskpolicy --live "allow mtk_hal_camera devmap_device chr_file { read write open ioctl getattr }"`.
4. **A standalone binary has no binder thread pool**: the camera service then blocks forever dequeueing buffers
   from your surface. Apps get one from the runtime; m7cam starts one through libbinder
   (`ProcessState::self()->startThreadPool()`).
5. Pass real (empty) capture-session callbacks: a NULL `onClosed` crashes in the session destructor.
6. `TEMPLATE_RECORD` delivers no frames into the encoder surface on this HAL; `TEMPLATE_PREVIEW` does.
7. MediaTek's encoder doesn't always set the keyframe flag; m7cam also looks for IDR NAL units.
8. Create the encoder by name (`OMX.MTK.VIDEO.ENCODER.AVC`): `createEncoderByType` enumerates every codec first.
9. libhybris' camera compat layer from the Halium (mako) image crashes in `set_preview_texture` on this device;
   the NDK route avoids GL and libhybris altogether.

## Home Assistant

Settings → Devices & services → Add integration → **Generic Camera**: stream source
`rtsp://<tablet>:8554/camera`, username and password from `cam.json`, advanced: RTSP transport TCP, frame rate 15.
Note that a dashboard card that shows the camera keeps it on while the dashboard is open.
