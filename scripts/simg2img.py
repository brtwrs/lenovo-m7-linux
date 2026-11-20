# Minimal Android sparse image -> raw image converter (no dependencies).
import struct, sys
src, dst = sys.argv[1], sys.argv[2]
f = open(src, 'rb'); o = open(dst, 'wb')
magic, maj, mnr, fhs, chs, bs, tb, tc, crc = struct.unpack('<IHHHHIIII', f.read(28))
assert magic == 0xED26FF3A
f.seek(fhs)
for _ in range(tc):
    ct, _r, cs, ts = struct.unpack('<HHII', f.read(chs))
    n = ts - chs
    if ct == 0xCAC1: o.write(f.read(n))                      # raw
    elif ct == 0xCAC2: fill = f.read(4); o.write(fill * (cs * bs // 4))  # fill
    elif ct == 0xCAC3: o.seek(cs * bs, 1)                   # don't care
    elif ct == 0xCAC4: f.read(n)                            # crc
o.truncate(tb * bs); o.close()
