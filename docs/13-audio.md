# 13. Audio

Speaker and microphone work in Linux mode, through **Android's own `audioserver`**. Linux programs play to
PulseAudio as usual.

Direct ALSA is a dead end on this kernel:
* **mmap** access to the MTK PCM (what most players and PulseAudio's ALSA module use) gives a kernel Oops
  (`snd_pcm_mmap_data_fault`), and the tablet reboots.
* Plain read/write gives silence (and the microphone delivers exact zeros): the audio front end is only powered up
  by Android's audio HAL, not by mixer controls.

So the HAL does the work, and Linux hands it PCM:

```
Linux (Debian chroot)                                                   Android side (bionic)
apps ─▶ PulseAudio null sink "m7" ── monitor ── unix socket ──▶ m7audio play ─▶ AAudio ─▶ audioserver ─▶ speaker
        (/etc/asound.conf: default = pulse)     /run/m7pulse/pcm (0700)
```

* `m7audio` opens the AAudio output (and so the amplifier) only on non-silent audio, and closes it after 3 s of
  silence.
* Without system_server nobody initialises the stream volumes: they sit at **-inf** (`dumpsys
  media.audio_flinger` shows `3:-inf`), so you hear nothing at all. `m7audio volume <0-15>` sets them through
  `AudioSystem::initStreamVolume` / `setStreamVolumeIndex`; `android-start.sh` does that at boot (default 8,
  or the number in `/data/adb/m7media/volume`).
* AAudio with `PERFORMANCE_MODE_NONE`: never the MMAP path.

## Setup

Build and install the Android side as in [chapter 12](12-camera.md) (`android-side/build.sh`, files in
`/data/adb/m7media`, `touch /root/autostart-media`). Then in Debian:

```sh
apt install --no-install-recommends pulseaudio pulseaudio-utils libasound2-plugins
systemctl --global disable pulseaudio.service pulseaudio.socket      # we start our own instance
mkdir -p /root/m7-audio && cp services/m7-audio/m7.pa services/m7-audio/pulse-start.sh /root/m7-audio/
printf "default-server = unix:/run/m7pulse/native\nautospawn = no\n" > /etc/pulse/client.conf.d/m7.conf
# make every ALSA program go through PulseAudio, so nothing ever opens hw:0 (mmap = kernel Oops)
printf "pcm.!default { type pulse }\nctl.!default { type pulse }\n" > /etc/asound.conf
```

Start PulseAudio from your app's start script:

```sh
pgrep -x pulseaudio >/dev/null || setsid /root/m7-audio/pulse-start.sh </dev/null >/tmp/pulse.log 2>&1 &
```

Test: `paplay some.wav`. Or measure without listening: on the Android side start `m7audio measure 7`, then
play a 880 Hz tone with `paplay` within a second; the printed tone level jumps from ~0 to tens or hundreds.
`m7audio selftest` does the same on its own (plays and records).

## Microphone

Recording works through AAudio as well (`m7audio measure` uses it). It isn't bridged to PulseAudio yet.
