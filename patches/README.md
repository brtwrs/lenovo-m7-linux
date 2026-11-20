# Patches

| File | Upstream | Base commit | What |
|---|---|---|---|
| `libhybris.diff` | https://github.com/libhybris/libhybris | `7079712` | buffer age 0; client display for `createWlBuffer` |
| `wlroots.diff` | https://github.com/droidian/wlroots (branch `bookworm`) | `599e4aa` | 1×1 pbuffer for Mali-400; no partial damage; buffer age −1; `glFinish` before swap |
| `cage.diff` | https://github.com/cage-kiosk/cage | `aa91af3` (0.1.3) | builds against Droidian wlroots; root allowed; no direct scan-out; forwards `wl_touch.frame` |

Apply with `git apply <file>` in a checkout of the base commit (the build scripts in `../scripts` do this).
The patched projects keep their own licenses (libhybris: Apache-2.0, wlroots: MIT, cage: MIT).
