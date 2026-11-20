#!/usr/bin/env python3
"""Make the 2048-byte images for the `para` (misc) partition.

  make-para.py recovery  bcb-boot-recovery.bin   -> every boot goes through recovery (= Magisk boot)
  make-para.py empty     para-empty.bin          -> normal boot again (undo / escape a boot loop)

Layout = Android bootloader_message: command[32], status[32], recovery[768], ...; we only set `command`
and `recovery` ("recovery\n"), exactly what `recovery --update_package` style tools write.
"""
import sys
mode, out = sys.argv[1], sys.argv[2]
d = bytearray(2048)
if mode == "recovery":
    d[0:13] = b"boot-recovery"
    d[64:73] = b"recovery\n"
elif mode != "empty":
    sys.exit("mode must be 'recovery' or 'empty'")
open(out, "wb").write(d)
print("written", out)
