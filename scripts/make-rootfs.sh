#!/bin/sh
# Build a Debian 12 (bookworm) armhf rootfs tarball on any Linux PC with Docker (qemu-user/binfmt for arm).
# Output: debian-armhf.tar  -> copy to the tablet and unpack into /data/linux (see docs/03-debian-rootfs.md)
set -e
docker run --rm --platform linux/arm/v7 -v "$PWD:/out" debian:bookworm-slim sh -c '
  apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    openssh-server wpasupplicant udhcpc iproute2 ca-certificates nano less procps psmisc && \
  apt-get clean && rm -rf /var/lib/apt/lists/* && \
  tar --one-file-system -C / --exclude=./out --exclude=./proc --exclude=./sys --exclude=./dev -cf /out/debian-armhf.tar .'
ls -la debian-armhf.tar
