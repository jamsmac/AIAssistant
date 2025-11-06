#!/bin/bash

# Setup automated backups with cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/enterprise_backup.sh"

# Create cron job for backups
# Daily at 2 AM
CRON_JOB="0 2 * * * ${BACKUP_SCRIPT} >> /var/log/backup_cron.log 2>&1"

# Check if cron job exists
(crontab -l 2>/dev/null | grep -q "${BACKUP_SCRIPT}") && {
    echo "✅ Backup cron job already exists"
} || {
    # Add cron job
    (crontab -l 2>/dev/null; echo "${CRON_JOB}") | crontab -
    echo "✅ Backup cron job added: Daily at 2 AM"
}

# Also create systemd timer for more reliability
sudo tee /etc/systemd/system/aiassistant-backup.service > /dev/null << EOF
[Unit]
Description=AIAssistant Backup Service
After=network.target

[Service]
Type=oneshot
User=$(whoami)
ExecStart=${BACKUP_SCRIPT}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/aiassistant-backup.timer > /dev/null << EOF
[Unit]
Description=AIAssistant Daily Backup Timer
Requires=aiassistant-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable systemd timer
sudo systemctl daemon-reload
sudo systemctl enable aiassistant-backup.timer
sudo systemctl start aiassistant-backup.timer

echo "✅ Systemd timer configured and started"
echo "📊 Check timer status: systemctl status aiassistant-backup.timer"
echo "📝 View backup logs: journalctl -u aiassistant-backup.service"