#!/usr/bin/env python3
"""Turn an frp partition dump into one with OEM unlock allowed (Lenovo Tab M7, MT8321).

Last byte = 1, first 32 bytes = sha256(32 zero bytes + rest).
Usage: python3 frp-unlock.py frp.bin frp-unlock.bin
"""
import hashlib
import sys

src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, "rb").read())

# Check: the formula must hold on the original, otherwise refuse to write.
if hashlib.sha256(bytes(32) + d[32:]).digest() != d[:32]:
    sys.exit("digest does not match the original; different layout, stopping")

print("unlock byte was:", d[-1])
d[-1] = 1
d[:32] = hashlib.sha256(bytes(32) + d[32:]).digest()
open(dst, "wb").write(d)
print("written:", dst, len(d), "bytes")
