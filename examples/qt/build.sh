#!/bin/sh
# Build the launcher on the tablet (Debian chroot).
set -e
apt-get install -y --no-install-recommends g++ qtdeclarative5-dev libqt5gui5 qml-module-qtquick2 qml-module-qtquick-window2 \
  qtwayland5 libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-libav
/usr/lib/qt5/bin/moc m7-launcher.cpp -o m7-launcher.moc
g++ -O2 -fPIC m7-launcher.cpp -o m7-launcher $(pkg-config --cflags --libs Qt5Quick Qt5Qml Qt5Gui gstreamer-1.0 gstreamer-app-1.0)
mkdir -p /root/qml && cp m7-launcher main.qml /root/qml/
