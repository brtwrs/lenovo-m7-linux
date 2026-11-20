# 5. Wifi

The wifi is part of MediaTek's "connsys" combo chip (wifi/BT/GPS/FM). Android init already loads the kernel
modules and firmware at boot (class `core`): `wmt_drv.ko` → `wmt_loader` → `wmt_launcher -p /vendor/firmware/`
sets `vendor.connsys.driver.ready=yes` → `wmt_chrdev_wifi.ko` + `wlan_drv_gen2.ko`. We keep that.

What Android's wifi HAL does next (found with strace) is tiny:
```sh
echo 1 > /dev/wmtWifi        # power on
echo STA > /dev/wmtWifi      # station mode → wlan0 appears
```
After that it is plain Linux: `ip link set wlan0 up`, `wpa_supplicant -D nl80211`, `udhcpc`. `echo 0` powers it off.

Notes:
* Android's policy routing hides the main routing table from processes; `ip rule add from all lookup main pref 9999`
  fixes that (done in `linux-boot.sh` and `chroot.sh`).
* Do **not** `rmmod` the wmt modules: the kernel crashes (watchdog reset).
* Under Linux the tablet uses its real MAC address (Android used a randomized one), so it gets a different DHCP lease.
