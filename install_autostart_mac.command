#!/bin/bash
# Run once on Mac - creates a LaunchAgent so it starts on login
cd "$(dirname "$0")"
PLIST="$HOME/Library/LaunchAgents/com.saha.teddyvoice.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.saha.teddyvoice</string>
<key>ProgramArguments</key><array><string>/usr/bin/python3</string><string>$PWD/assistant.py</string></array>
<key>RunAtLoad</key><true/>
<key>WorkingDirectory</key><string>$PWD</string>
</dict></plist>
EOF
launchctl load "$PLIST"
echo "Done. Teddy will start on login. To remove: launchctl unload $PLIST; rm $PLIST"
