#!/bin/bash
XVFB=/nix/store/ykck7gdd6szwrb3qnpb5y5fvjlnmzhz0-xorg-server-21.1.18/bin/Xvfb
X11VNC=/nix/store/4rxi8q5x6yb39ykygl5ddvmlx6v26gjy-x11vnc-0.9.17/bin/x11vnc
NOVNC=/nix/store/n7h60i6lqysmya4clas5vghfsjc6sspa-novnc-1.6.0/bin/novnc

# Start virtual display
$XVFB :99 -screen 0 1280x800x24 &>/dev/null &
XVFB_PID=$!
sleep 1

# Start VNC server on the virtual display (port 5900)
$X11VNC -display :99 -nopw -listen localhost -xkb -forever -shared &>/dev/null &
X11VNC_PID=$!
sleep 1

# Start noVNC with custom web dir (auto-connects index.html) on port 5000
$NOVNC --listen 5000 --vnc localhost:5900 --web novnc_web &>/dev/null &
NOVNC_PID=$!

# Launch the app
export DISPLAY=:99
export SKIP_ADMIN_CHECK=1
python main.py

kill $XVFB_PID $X11VNC_PID $NOVNC_PID 2>/dev/null
