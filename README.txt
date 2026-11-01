MINECRAFT 2.0 - CREATED BY CHANDRU
==================================

FILES
-----
main.py          Kivy game client with looping video title background
server.py        WebSocket multiplayer server (up to 10 players)
buildozer.spec   Starting Android APK configuration
requirements.txt Python dependencies
background.mp4  Add your own MP4 video with this exact filename

VIDEO BACKGROUND
----------------
Place background.mp4 in the same folder as main.py.
Use a video you created or have permission to use.
The video loops on the title screen and behind the game screen.
If the video is missing or the device cannot play it, the game uses
a plain fallback background.

LOCAL WI-FI TEST
----------------
1. Install Python on your laptop.
2. Install server package:
   python -m pip install websockets==12.0
3. Start server:
   python server.py
4. Find your laptop Wi-Fi IPv4 address:
   ipconfig
5. Edit SERVER_URL in main.py to:
   ws://YOUR_LAPTOP_IP:8765
6. Install client dependencies:
   python -m pip install kivy websocket-client ffpyplayer
7. Run the client:
   python main.py
8. Connect other devices on the same Wi-Fi using the same server address.
   Allow Python through Windows Firewall for private networks if prompted.

ONLINE PLAY
-----------
For friends outside your Wi-Fi, deploy server.py on a public host and use
a secure wss:// endpoint. Do not expose this unauthenticated prototype
directly to the public internet.

ANDROID APK
-----------
Buildozer is generally used through Linux. On Windows, use WSL2 with Ubuntu.
Follow the current official guide:
https://buildozer.readthedocs.io/en/latest/installation.html

The included ffpyplayer/video setup is a starting point, not a guarantee that
every Android build environment has a compatible video provider. Test video
playback on the target phone. If the Android build fails on ffpyplayer, first
build without video support and add Android-compatible video playback later.

PROJECT STATUS
--------------
This is an early 2D multiplayer prototype, not a finished 3D Minecraft game.
It demonstrates a looping video title screen, shared grid map, movement,
block placement and breaking. It does not yet include accounts, authentication,
chat, crafting, inventory, anti-cheat, persistent worlds or production security.


FIXES IN THIS REVISION
----------------------
- Fixed delayed connection-error callback handling in main.py.
- Prevented invalid non-object JSON messages from crashing the client/server.
- Close an existing WebSocket connection when returning to the title screen.
- Reset player state when starting a new session.
- Removed ffpyplayer from Android build requirements because it commonly
  causes Android packaging/build compatibility problems.
- The optional background.mp4 may use the available Android video provider;
  if unavailable, the game displays its fallback background.

IMPORTANT SERVER SETUP
----------------------
The client will not connect until a multiplayer server is running.
Change SERVER_URL in main.py to the actual reachable server address.
For same Wi-Fi, use ws://YOUR_SERVER_LAN_IP:8765.
For internet hosting, use a secure wss:// server address.
The server.py file must run on a computer or hosted server; it does not run
automatically just because the Android APK is installed.
