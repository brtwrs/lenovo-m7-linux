# 9. Apps

## Qt Quick (recommended)
Qt Quick renders straight to OpenGL ES 2 and is made for this class of hardware: 60 fps on the Mali-400 with
animations, where a browser struggles. Debian's Qt 5.15 for **armhf** is built for GLES, so it works with
libhybris as is. (On arm64 Debian's Qt uses desktop GL; there install `libqt5gui5-gles`.)

Build the launcher and the demo (`examples/qt`):
```sh
cd /root/m7-linux/examples/qt && sh build.sh       # → /root/qml/m7-launcher + main.qml
sh /root/m7-linux/scripts/qt-start.sh /root/qml/main.qml
```
To start it at boot: copy `scripts/qt-start.sh` to `/root/qml/qml-start.sh` and `touch /root/autostart-qml /root/autostart-gpu`.

`m7-launcher` does two things qmlscene cannot:
* it asks for a **24-bit** colour buffer (qmlscene got RGB565 → banding in gradients);
* it registers **`LiveVideo`** (`import M7 1.0`): an RTSP H.264 player as a QML item.

```qml
LiveVideo { anchors.fill: parent; source: "rtsp://camera/stream"; fps: 15; visible: playing }
```
It decodes in software with GStreamer (`avdec_h264`) into RGBx and hands every frame to Qt as an ordinary
texture. Measured: 720p30 decode ≈ 15 % CPU; displayed at 15 fps the app uses ≈ 33 %.

### Qt tips for this GPU
* **Never use QtMultimedia (`MediaPlayer`/`Video`)**: playbin also plays the audio track (even muted), and ALSA
  mmap playback crashes this kernel. `LiveVideo` takes the video track only.
* Blur is expensive on a Mali-400. A downscaled image (e.g. 96×60, linear filtering) used as background of
  translucent panels looks the same as a real blur and costs nothing. Downscale in steps (or average 4×4 in a
  shader), otherwise it shimmers.
* Scale a fixed design (e.g. 1920×1200) with `scale`, and give text a minimum *real* pixel size; thin font weights
  become hairlines on a 1024×600 panel.
* `QML_XHR_ALLOW_FILE_READ=1` lets QML read small config files with XMLHttpRequest.
* `ShaderEffect` gets colour uniforms *not* premultiplied.

## WPE WebKit kiosk (cog)
If you want web pages: WPE WebKit ≥ 2.44 with Skia uses the GPU through libhybris. Debian 12's WPE (2.38) is
too old; we ran WPE 2.54 / cog 0.18 from Debian testing/sid in a second chroot. Start with `scripts/gpu-cog.sh URL`.

> ⚠️ WebKit runs **as root without its sandbox** here (no user namespaces on this kernel). Only load your own,
> trusted pages from your own network, never the open internet.
Required: no bwrap sandbox (`WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1`, no user namespaces on 4.9), MSAA off,
and `--features=-PropagateDamagingInformation,-UnifyDamagedRegions` (otherwise WPE sometimes draws only the
changed element into an empty buffer). Simple pages run at 60 fps; heavy dashboards (blur, many images) reached
35–60 fps with stutters when images change. Chromium cannot use the GPU here (it wants ANGLE/DRM).
