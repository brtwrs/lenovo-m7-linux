/* Empty libmediaplayerservice.so for Halium's minimediaservice.
 * minimediaservice only calls android::MediaPlayerService::instantiate(); the camera doesn't need the
 * media player, and the real library from the mako image won't link against this device's libraries.
 * Built without libc, so Android's linker loads it without any further dependencies:
 *
 *   gcc -shared -fPIC -nostdlib -Wl,-soname,libmediaplayerservice.so -o libmediaplayerservice.so mediaplayerservice-stub.c
 *   (any armhf compiler works, e.g. on the tablet's Debian; or the NDK's clang with -nostdlib)
 */
void _ZN7android18MediaPlayerService11instantiateEv(void) {}
