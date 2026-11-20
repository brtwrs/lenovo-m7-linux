#!/bin/sh
# There is no udevd. libinput only uses devices that udev tagged, so write the udev database entries by hand.
# Seat ${1:-seat0}. event2 = mtk-tpd (touch), event1 = mtk-kpd (Vol-, Vol+, Power).
# The calibration matrix maps the portrait panel (600x1024) to the 90-degree rotated landscape output (cage -r).
SEAT=${1:-seat0}; mkdir -p /run/udev/data
printf "E:ID_INPUT=1\nE:ID_INPUT_TOUCHSCREEN=1\nE:ID_SEAT=$SEAT\nE:LIBINPUT_CALIBRATION_MATRIX=0 -1 1 1 0 0\nG:seat\n" > /run/udev/data/c$(cat /sys/class/input/event2/dev)
printf "E:ID_INPUT=1\nE:ID_INPUT_KEY=1\nE:ID_SEAT=$SEAT\nG:seat\n" > /run/udev/data/c$(cat /sys/class/input/event1/dev)
