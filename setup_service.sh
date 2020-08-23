#!/usr/bin/env bash

HOMEDIR="$(dirname "$(realpath "$0")")"

# Install requirements
pip3 install -r "$HOMEDIR/requirements.txt"

# Create systemd dir
mkdir -p "$HOME/.config/systemd/user"

# Create host service
echo "-- Configuring host service"
cat > "$HOME/.config/systemd/user/ash-host.service" << EOF
[Unit]
Description=Start ASH host service
Wants=mosquitto.service

[Service]
WorkingDirectory=$HOMEDIR
ExecStart=/usr/bin/python3 -m host.main --tx2

[Install]
WantedBy=default.target
EOF
systemctl --user enable ash-host.service

# Create logging service
echo "-- Configuring recorder service"
cat > "$HOME/.config/systemd/user/ash-recorder.service" << EOF
[Unit]
Description=Start ASH service
Wants=mosquitto.service

[Service]
WorkingDirectory=$HOMEDIR
ExecStart=/usr/bin/python3 -m recorder.main INFO body/#

[Install]
WantedBy=default.target
EOF
systemctl --user enable ash-recorder.service

echo "-- Reloading services..."
systemctl --user daemon-reload
systemctl --user start ash-host.service
systemctl --user start ash-recorder.service

