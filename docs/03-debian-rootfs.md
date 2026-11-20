# 3. The Debian rootfs

Debian 12 (bookworm) **armhf** in `/data/linux` on the data partition (≈ 13 GB free there).

## Build
On a PC with Docker and arm emulation:
```sh
sh scripts/make-rootfs.sh          # → debian-armhf.tar (openssh, wpasupplicant, udhcpc, iproute2, …)
```

## Install
```sh
adb push debian-armhf.tar /data/local/tmp/
adb shell su -c 'mkdir -p /data/linux && cd /data/linux && /data/adb/magisk/busybox tar xf /data/local/tmp/debian-armhf.tar'
adb push scripts/chroot.sh /data/local/tmp/
adb shell su -c 'sh /data/local/tmp/chroot.sh'     # you are now root in Debian
```
`chroot.sh` mounts proc/sys/dev/devpts/tmp, binds `/vendor` and `/system` (needed later for the GPU driver),
unsets Android's `LD_PRELOAD`/`TMPDIR`, and tells apt not to drop privileges (`APT::Sandbox::User "root"`;
there is no `_apt` sandbox on this kernel).

## Inside Debian
* Put your ssh public key in `/root/.ssh/authorized_keys`. `sshd` will run on **port 2222**.
* Put your wifi in `/etc/wpa_supplicant/wpa.conf` (see `scripts/wpa.conf.example`).
* Copy this repo to `/root/m7-linux` (the scripts expect that path).
