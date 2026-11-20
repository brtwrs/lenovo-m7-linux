# 2. Unlock the bootloader and root

> **This wipes all data on the tablet.** Make the backup in step 2; it is your only way back.

The TB-7305F refuses `fastboot flashing unlock` ("Unlock operation is not allowed") until the **frp** partition
says OEM unlock is allowed. The grey "OEM unlocking" switch in developer options stays grey even when it worked;
the bootloader only looks at a byte in frp. We set that byte through the MediaTek BootROM (BROM) with mtkclient.

## 1. BROM mode (the button trick)
1. Unplug the USB cable. Hold **Power** ≈ 15 s until the screen stays black (tablet off).
2. On the PC, start the mtkclient command you want to run; wait until it says *Waiting for device*.
3. Hold **Vol+ and Vol−** together and plug in the cable. The screen stays black; mtkclient connects.

On macOS run mtkclient with `sudo`. BROM only lives a few seconds: run mtkclient directly on the machine the
tablet is plugged into (USB passthrough into VMs/containers was too slow in our tests).

## 2. Backup everything except the big partitions
```sh
python3 mtk.py rl ~/m7-backup --skip userdata,system,vendor,product,cache
```

## 3. Allow OEM unlock in frp
The frp partition ends with the unlock flag, and starts with a sha256 over the rest:
`first 32 bytes = sha256(32 zero bytes + data[32:])`. `scripts/frp-unlock.py` sets the last byte to 1 and fixes
the digest, after checking that the formula holds on your original (it refuses otherwise):
```sh
python3 scripts/frp-unlock.py ~/m7-backup/frp.bin ~/m7-backup/frp-unlock.bin
python3 mtk.py w frp ~/m7-backup/frp-unlock.bin          # BROM again
```
Boot normally and check: `adb shell getprop sys.oem_unlock_allowed` must print `1`.

## 4. Unlock
```sh
adb reboot bootloader
fastboot flashing unlock        # confirm with Vol+; this WIPES the tablet
```
`fastboot reboot` may hang: hold Power 10 s. Set up Android again (skip wifi/account), enable USB debugging.

## 5. Root: Magisk in **recovery**
This device is *legacy system-as-root* (A-only, `ro.build.system_root_image=true`): the kernel ignores the boot
ramdisk, so Magisk must be patched into **recovery**, and you get root when the device boots "via recovery".

1. Install Magisk (tested v31.1, `armeabi-v7a`) and copy `recovery.bin` from your backup to `/sdcard/Download`.
2. Patch it without the app: from the APK take `assets/boot_patch.sh`, `assets/util_functions.sh` and
   `lib/armeabi-v7a/lib{magiskboot,magisk,magiskinit,init-ld,busybox,magiskpolicy}.so` (rename without `lib`/`.so`)
   into `/data/local/tmp/mp`, then `RECOVERYMODE=true ./busybox sh boot_patch.sh recovery.img` → `new-boot.img`.
3. Flash it as recovery: `fastboot flash recovery magisk-recovery.img`.
4. `adb reboot recovery` now starts Android **with** Magisk (`ro.bootmode=recovery`).

### Make every boot a Magisk boot
Android's `flash_recovery` restores the stock recovery on every normal boot. To boot into the Magisk recovery
*every* time, write a bootloader control block ("boot-recovery") into the `para` partition once:
`python3 scripts/make-para.py recovery bcb-boot-recovery.bin && fastboot flash para bcb-boot-recovery.bin`. From then on
every (re)boot is a Magisk boot, and `flash_recovery` leaves the recovery alone in that mode.

If you ever end up in a boot loop, BROM + `python3 mtk.py w para para-empty.bin` (made with `make-para.py empty para-empty.bin`)
brings back a normal boot.

### Shell root
Magisk silently rejects `su` from adb until you allow it: Magisk → Superuser → **+** → tick *Shell*.
If the Magisk app says "environment incomplete", accept its additional setup.
