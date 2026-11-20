#!/bin/sh
# Start a Qt Quick app full-screen on the GPU: cage (Wayland, hwcomposer backend) + the launcher from examples/qt.
# Install as /root/qml/qml-start.sh and create /root/autostart-qml + /root/autostart-gpu to start it at boot.
. /opt/hybris/env.sh
export LD_LIBRARY_PATH=/opt/wlr/lib/arm-linux-gnueabihf:/opt/hybris/lib XDG_RUNTIME_DIR=/tmp/xdg LANG=C.UTF-8
export WLR_BACKENDS=hwcomposer,libinput XDG_SEAT=seat1 EGL_PLATFORM=hwcomposer
/root/m7-linux/scripts/udev-fake.sh seat1; mkdir -p /tmp/xdg; chmod 700 /tmp/xdg
exec /opt/wlr/bin/cage -r -- /usr/bin/env EGL_PLATFORM=wayland QT_QPA_PLATFORM=wayland-egl QT_WAYLAND_DISABLE_WINDOWDECORATION=1 \
  QML_XHR_ALLOW_FILE_READ=1 /root/qml/m7-launcher ${1:-/root/qml/main.qml}
