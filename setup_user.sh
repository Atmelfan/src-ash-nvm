#!/usr/bin/env bash

# This script creates a new user and group for
# the ash service application
#
# Usage ./setup_user.sh [<remote>]

SCRIPT=$(realpath "$0")
ASH_USER="ash"
ASH_HOME="/home/ash"

if [ $# -ne 0 ]; then
  echo "-- Copying setup script to target"
  scp "$SCRIPT" "$1:/tmp"
  echo "-- Executing setup script..."
  ssh -t "$1" "sudo /tmp/$(basename "$SCRIPT")"
else
  # Create user and add permissions
  echo "-- Creating new user '$ASH_USER'"
  adduser \
    --system \
    --disabled-password \
    --group \
    --shell /bin/bash \
    --gecos "Runtime user account" \
    --home $ASH_HOME \
    $ASH_USER || exit 1
  adduser $ASH_USER dialout
  adduser $ASH_USER systemd-journal
  loginctl enable-linger $ASH_USER || exit 3

  # Copy authorized keys
  if [ -f "$HOME/.ssh/authorized_keys" ]; then
    echo "-- Copying SSH keys to new user..."
    mkdir -p "$ASH_HOME/.ssh"
    tee -a "$ASH_HOME/.ssh/authorized_keys" < "$HOME/.ssh/authorized_keys"
  else
    echo "-- No SSH keys available on current user"
  fi

  # Disable unnecessary services
  echo "-- Disabling unnecessary services..."
  systemctl disable nv-l4t-usb-device-mode.service
  systemctl mask serial-getty@ttyGS0.service
  systemctl mask dev-ttyGS0.device
  systemctl set-default multi-user.target

  # Install mosquitto
  apt-get install mosquitto
  cat > /etc/mosquitto/conf.d/adafruit-io-bridge.conf << EOF
# Connection name
connection adafruit

# Secure SSL/TLS
address io.adafruit.com:8883
# adjust path as approriate to point to directory with PEM encoded .crt CA files
bridge_capath /etc/ssl/certs/

# For CentOS 7 (and other RHEL derivatives), use this directive instead of bridge_capath
# bridge_cafile /etc/ssl/certs/ca-bundle.crt

# Insecure
# address io.adafruit.com:1883

# Credentials
remote_username Atmelfan
remote_password <password>

# Config options for bridge
start_type automatic
bridge_protocol_version mqttv311

# This is important, if set to True connection will fail,
# probably because users don't have permissions to $SYS/#
notifications false

# Also important. if set to True the connection will fail,
# it seems io.adafruit.com doesn't support this
try_private false

# Topics to bridge
# topic <local topic> <in|out|both> <QoS> <local topic prefix> <remote topic prefix>

# eg: bridge temperature/shed to temperature/shed
#topic 1min out 0 host/jetson/load Atmelfan/feeds

# eg: bridge to io.adafruit.com
# temperature/shed to <username>/feeds/temperature_shed
topic 1min out 0 host/jetson/load/ Atmelfan/feeds/load_
topic used out 0 host/jetson/mem/ Atmelfan/feeds/mem_
topic freq out 0 host/jetson/cpu/0/ Atmelfan/feeds/cpu0_
topic freq out 0 host/jetson/cpu/1/ Atmelfan/feeds/cpu1_
topic freq out 0 host/jetson/cpu/2/ Atmelfan/feeds/cpu2_
topic freq out 0 host/jetson/cpu/3/ Atmelfan/feeds/cpu3_
topic voltage out 0 host/jetson/rail/vdd_in/ Atmelfan/feeds/battery_
topic temp out 0 host/jetson/temp/mcpu-therm/ Atmelfan/feeds/module_

# eg: bridge from io.adafruit.com
# <username>/feeds/throttle to adafruit.io/throttle
topic throttle in 0 adafruit.io/ Atmelfan/feeds/
topic test in 0 adafruit.io/ Atmelfan/feeds/

#
# eg: bi-directional topic
# <username>/feeds/welcome-feed to/from adafruit.io/welcome-feed
# topic welcome-feed both 0 adafruit.io/ <username>/feeds/

# note: if using the Adafruit.io "Welcome Feed" you'll need to rename
#       it to "welcome-feed" in the web interface for the above example to work
EOF

  # Reboot to start systemd etc for user
  echo "-- Rebooting..."
  reboot
fi




