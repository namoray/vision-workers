cat <<EOF >/etc/systemd/system/vision-autoupdater.service
[Unit]
Description=Orchestrator AutoUpdater
After=network.target
StartLimitIntervalSec=30
StartLimitBurst=2

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$HOME/vision-workers
ExecStart=python -u run_autoupdates_validator.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# load it and start
systemctl daemon-reload
systemctl enable --now vision-autoupdater
systemctl restart vision-autoupdater
