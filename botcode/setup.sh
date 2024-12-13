#!/bin/bash
yum update -y
yum install -y gcc make python3-pip git wget curl pulseaudio 
pip3 install selenium webdriver-manager boto3

# Start PulseAudio
pulseaudio --start

# Load Virtual Sink
pactl load-module module-null-sink sink_name=Virtual_Sink
pactl set-default-sink Virtual_Sink
