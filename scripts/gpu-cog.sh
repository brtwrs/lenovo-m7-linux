#!/bin/sh
# Alternative to Qt: a WPE WebKit kiosk (cog) on the GPU. Needs WPE >= 2.44 with Skia (Debian testing/sid);
# see docs/09-apps.md. Usage: gpu-cog.sh URL
. /opt/hybris/env.sh
export LD_LIBRARY_PATH=/opt/wlr/lib/arm-linux-gnueabihf:/opt/hybris/lib XDG_RUNTIME_DIR=/tmp/xdg LANG=C.UTF-8
export WLR_BACKENDS=hwcomposer,libinput XDG_SEAT=seat1 EGL_PLATFORM=hwcomposer
/root/m7-linux/scripts/udev-fake.sh seat1; mkdir -p /tmp/xdg; chmod 700 /tmp/xdg
# - no bwrap sandbox (no user namespaces on the 4.9 kernel)
# - MSAA off (stutters on Mali-400)
# - damage propagation off: otherwise WPE sometimes draws only the changed element into an empty buffer
exec /opt/wlr/bin/cage -r -- /usr/bin/env EGL_PLATFORM=wayland WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1 \
  WEBKIT_SKIA_ENABLE_DYNAMIC_MSAA=0 WEBKIT_SKIA_MSAA_SAMPLE_COUNT=0 \
  cog -P wl --features=-PropagateDamagingInformation,-UnifyDamagedRegions "$1"
