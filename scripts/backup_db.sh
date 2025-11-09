#!/bin/bash
###############################################################################
# Database Backup Script
#
# Backs up SQLite databases to Railway storage or S3
# Run this script daily via cron or Railway scheduled task
###############################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/app/data/backups}"
DATA_DIR="${DATA_DIR:-/app/data}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting database backup..."

# Backup SQLite databases
databases=("history.db" "autopilot_cache.db" "test_history.db")

for db in "${databases[@]}"; do
    db_path="$DATA_DIR/$db"

    if [ -f "$db_path" ]; then
        backup_file="$BACKUP_DIR/${db%.db}_$DATE.db"

        log "Backing up $db..."

        # Use sqlite3 .backup command for safe hot backup
        if command -v sqlite3 &> /dev/null; then
            sqlite3 "$db_path" ".backup '$backup_file'"

            # Verify backup integrity
            if sqlite3 "$backup_file" "PRAGMA integrity_check;" | grep -q "ok"; then
                log "✓ Backup successful: $backup_file"

                # Get file size
                size=$(du -h "$backup_file" | cut -f1)
                log "  Size: $size"
            else
                error "Backup integrity check failed for $db"
                rm -f "$backup_file"
                exit 1
            fi
        else
            # Fallback to simple copy if sqlite3 not available
            warn "sqlite3 command not found, using simple copy"
            cp "$db_path" "$backup_file"
            log "✓ Backup copied: $backup_file"
        fi
    else
        warn "Database not found: $db_path (skipping)"
    fi
done

# Clean up old backups (keep last N days)
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*.db" -type f -mtime +$RETENTION_DAYS -delete
log "✓ Cleanup complete"

# Upload to S3 if configured
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$S3_BUCKET" ]; then
    log "Uploading to S3 bucket: $S3_BUCKET..."

    if command -v aws &> /dev/null; then
        for db in "${databases[@]}"; do
            backup_file="$BACKUP_DIR/${db%.db}_$DATE.db"
            if [ -f "$backup_file" ]; then
                s3_path="s3://$S3_BUCKET/backups/$(basename $backup_file)"
                aws s3 cp "$backup_file" "$s3_path"
                log "✓ Uploaded to $s3_path"
            fi
        done
    else
        warn "AWS CLI not installed, skipping S3 upload"
    fi
fi

# Generate backup report
report_file="$BACKUP_DIR/backup_report_$DATE.txt"
cat > "$report_file" << EOF
Database Backup Report
======================
Date: $(date)
Host: $(hostname)
Environment: ${ENVIRONMENT:-development}

Databases Backed Up:
EOF

for db in "${databases[@]}"; do
    backup_file="$BACKUP_DIR/${db%.db}_$DATE.db"
    if [ -f "$backup_file" ]; then
        size=$(du -h "$backup_file" | cut -f1)
        echo "  ✓ $db ($size)" >> "$report_file"
    else
        echo "  ✗ $db (not found)" >> "$report_file"
    fi
done

echo "" >> "$report_file"
echo "Total backups in storage: $(ls -1 $BACKUP_DIR/*.db 2>/dev/null | wc -l)" >> "$report_file"
echo "Disk usage: $(du -sh $BACKUP_DIR | cut -f1)" >> "$report_file"

log "✓ Backup report saved: $report_file"
cat "$report_file"

log "Backup process completed successfully!"

# Optional: Send notification (if webhook configured)
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    curl -X POST "$BACKUP_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"status\":\"success\",\"date\":\"$DATE\",\"report\":\"$(cat $report_file | sed 's/"/\\"/g' | tr '\n' ' ')\"}" \
        &> /dev/null || warn "Failed to send webhook notification"
fi

exit 0
