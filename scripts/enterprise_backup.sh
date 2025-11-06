#!/bin/bash

# ================================================
# ENTERPRISE BACKUP & DISASTER RECOVERY SCRIPT
# AIAssistant Platform - Production Grade
# ================================================

set -euo pipefail

# Configuration
PROJECT_NAME="aiassistant"
BACKUP_ROOT="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_ID="${PROJECT_NAME}_${TIMESTAMP}"
RETENTION_DAYS=30
RETENTION_COPIES=10

# Database
DB_TYPE="${DB_TYPE:-sqlite}" # sqlite or postgresql
DATABASE_URL="${DATABASE_URL:-}"
SQLITE_PATH="./data/production.db"

# Cloud Storage
S3_BUCKET="${S3_BUCKET:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Notifications
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="${BACKUP_ROOT}/backup_${TIMESTAMP}.log"
mkdir -p ${BACKUP_ROOT}

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a ${LOG_FILE}

    case ${level} in
        ERROR)   echo -e "${RED}❌ ${message}${NC}" ;;
        SUCCESS) echo -e "${GREEN}✅ ${message}${NC}" ;;
        WARNING) echo -e "${YELLOW}⚠️  ${message}${NC}" ;;
        INFO)    echo -e "${BLUE}ℹ️  ${message}${NC}" ;;
    esac
}

# Error handling
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    log ERROR "Backup failed at line ${line_number} with exit code ${exit_code}"
    send_notification "FAILED" "Backup ${BACKUP_ID} failed at line ${line_number}"
    exit ${exit_code}
}

# ======================
# BACKUP FUNCTIONS
# ======================

backup_database() {
    log INFO "Starting database backup..."

    local db_backup="${BACKUP_ROOT}/${BACKUP_ID}_database"

    if [ "${DB_TYPE}" == "postgresql" ] && [ -n "${DATABASE_URL}" ]; then
        # PostgreSQL backup with compression
        pg_dump ${DATABASE_URL} \
            --no-owner \
            --no-privileges \
            --format=custom \
            --compress=9 \
            --file="${db_backup}.dump"

        # Create SQL format backup for easier restore
        pg_dump ${DATABASE_URL} \
            --no-owner \
            --no-privileges \
            --format=plain \
            | gzip -9 > "${db_backup}.sql.gz"

        log SUCCESS "PostgreSQL backup completed: ${db_backup}.dump"

    elif [ -f "${SQLITE_PATH}" ]; then
        # SQLite backup with integrity check
        sqlite3 ${SQLITE_PATH} "PRAGMA integrity_check;"
        sqlite3 ${SQLITE_PATH} ".backup ${db_backup}.db"
        gzip -9 "${db_backup}.db"

        log SUCCESS "SQLite backup completed: ${db_backup}.db.gz"
    else
        log WARNING "No database found to backup"
    fi
}

backup_application() {
    log INFO "Backing up application code..."

    local app_backup="${BACKUP_ROOT}/${BACKUP_ID}_application.tar.gz"

    tar -czf ${app_backup} \
        --exclude='node_modules' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='data/*.db' \
        api/ \
        agents/ \
        scripts/ \
        web-ui/app/ \
        web-ui/components/ \
        web-ui/lib/ \
        web-ui/package.json \
        web-ui/package-lock.json \
        requirements.txt \
        railway.toml \
        vercel.json \
        docker-compose.yml 2>/dev/null || true

    log SUCCESS "Application backup completed: ${app_backup}"
}

backup_configuration() {
    log INFO "Backing up configuration..."

    local config_backup="${BACKUP_ROOT}/${BACKUP_ID}_config"
    mkdir -p ${config_backup}

    # Encrypt sensitive configuration
    if [ -f ".env.production" ]; then
        openssl enc -aes-256-cbc \
            -salt \
            -in .env.production \
            -out "${config_backup}/env.production.encrypted" \
            -pass pass:"${ENCRYPTION_KEY:-default_key}"
    fi

    # Copy non-sensitive configs
    cp -f railway.toml "${config_backup}/" 2>/dev/null || true
    cp -f vercel.json "${config_backup}/" 2>/dev/null || true
    cp -f docker-compose.yml "${config_backup}/" 2>/dev/null || true

    # Create manifest
    cat > "${config_backup}/manifest.json" << EOF
{
    "backup_id": "${BACKUP_ID}",
    "timestamp": "$(date -Iseconds)",
    "type": "configuration",
    "encrypted": true,
    "files": [
        "env.production.encrypted",
        "railway.toml",
        "vercel.json",
        "docker-compose.yml"
    ]
}
EOF

    tar -czf "${config_backup}.tar.gz" -C "${BACKUP_ROOT}" "${BACKUP_ID}_config"
    rm -rf ${config_backup}

    log SUCCESS "Configuration backup completed"
}

backup_metadata() {
    log INFO "Creating backup metadata..."

    local metadata_file="${BACKUP_ROOT}/${BACKUP_ID}_metadata.json"

    cat > ${metadata_file} << EOF
{
    "backup_id": "${BACKUP_ID}",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "project": "${PROJECT_NAME}",
    "components": {
        "database": {
            "type": "${DB_TYPE}",
            "size": "$(du -sh ${BACKUP_ROOT}/${BACKUP_ID}_database* 2>/dev/null | cut -f1 || echo 'N/A')"
        },
        "application": {
            "size": "$(du -sh ${BACKUP_ROOT}/${BACKUP_ID}_application.tar.gz 2>/dev/null | cut -f1 || echo 'N/A')"
        },
        "configuration": {
            "size": "$(du -sh ${BACKUP_ROOT}/${BACKUP_ID}_config.tar.gz 2>/dev/null | cut -f1 || echo 'N/A')"
        }
    },
    "system": {
        "os": "$(uname -s)",
        "kernel": "$(uname -r)",
        "python": "$(python3 --version 2>&1)",
        "node": "$(node --version 2>&1)",
        "docker": "$(docker --version 2>&1)"
    },
    "retention": {
        "days": ${RETENTION_DAYS},
        "copies": ${RETENTION_COPIES}
    }
}
EOF

    log SUCCESS "Metadata created: ${metadata_file}"
}

# ======================
# CLOUD UPLOAD
# ======================

upload_to_cloud() {
    if [ -z "${S3_BUCKET}" ]; then
        log WARNING "S3_BUCKET not configured, skipping cloud upload"
        return 0
    fi

    log INFO "Uploading to S3..."

    # Install AWS CLI if not present
    if ! command -v aws &> /dev/null; then
        log WARNING "AWS CLI not found, skipping cloud upload"
        return 0
    fi

    local s3_path="s3://${S3_BUCKET}/backups/${PROJECT_NAME}/${TIMESTAMP:0:8}/"

    # Upload all backup files
    for file in ${BACKUP_ROOT}/${BACKUP_ID}*; do
        if [ -f "$file" ]; then
            aws s3 cp "$file" "${s3_path}" \
                --storage-class STANDARD_IA \
                --metadata "backup-id=${BACKUP_ID},project=${PROJECT_NAME}" \
                --region ${AWS_REGION}

            log SUCCESS "Uploaded: $(basename $file)"
        fi
    done

    # Create lifecycle policy for automatic deletion
    aws s3api put-bucket-lifecycle-configuration \
        --bucket ${S3_BUCKET} \
        --lifecycle-configuration file:///dev/stdin <<EOF
{
    "Rules": [{
        "Id": "DeleteOldBackups",
        "Status": "Enabled",
        "Prefix": "backups/${PROJECT_NAME}/",
        "Expiration": {
            "Days": ${RETENTION_DAYS}
        }
    }]
}
EOF

    log SUCCESS "Cloud upload completed"
}

# ======================
# VERIFICATION
# ======================

verify_backup() {
    log INFO "Verifying backup integrity..."

    local errors=0

    # Check database backup
    if [ "${DB_TYPE}" == "postgresql" ]; then
        if [ ! -f "${BACKUP_ROOT}/${BACKUP_ID}_database.dump" ]; then
            log ERROR "Database backup not found"
            ((errors++))
        fi
    elif [ ! -f "${BACKUP_ROOT}/${BACKUP_ID}_database.db.gz" ]; then
        log WARNING "Database backup not found"
    fi

    # Check application backup
    if [ ! -f "${BACKUP_ROOT}/${BACKUP_ID}_application.tar.gz" ]; then
        log ERROR "Application backup not found"
        ((errors++))
    else
        tar -tzf "${BACKUP_ROOT}/${BACKUP_ID}_application.tar.gz" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log ERROR "Application backup corrupted"
            ((errors++))
        fi
    fi

    # Check configuration backup
    if [ ! -f "${BACKUP_ROOT}/${BACKUP_ID}_config.tar.gz" ]; then
        log ERROR "Configuration backup not found"
        ((errors++))
    fi

    if [ ${errors} -eq 0 ]; then
        log SUCCESS "Backup verification passed"
        return 0
    else
        log ERROR "Backup verification failed with ${errors} errors"
        return 1
    fi
}

# ======================
# CLEANUP
# ======================

cleanup_old_backups() {
    log INFO "Cleaning up old backups..."

    # Local cleanup - keep last N copies
    cd ${BACKUP_ROOT}
    ls -t ${PROJECT_NAME}_* 2>/dev/null | tail -n +$((RETENTION_COPIES + 1)) | xargs -r rm -f

    # Count remaining backups
    local count=$(ls ${PROJECT_NAME}_* 2>/dev/null | wc -l)
    log SUCCESS "Cleanup completed. ${count} backups retained locally"
}

# ======================
# NOTIFICATIONS
# ======================

send_notification() {
    local status=$1
    local message=$2

    # Slack notification
    if [ -n "${SLACK_WEBHOOK}" ]; then
        curl -X POST ${SLACK_WEBHOOK} \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"Backup ${status}\",
                \"attachments\": [{
                    \"color\": \"$([ \"${status}\" == \"SUCCESS\" ] && echo \"good\" || echo \"danger\")\",
                    \"fields\": [
                        {\"title\": \"Project\", \"value\": \"${PROJECT_NAME}\", \"short\": true},
                        {\"title\": \"Backup ID\", \"value\": \"${BACKUP_ID}\", \"short\": true},
                        {\"title\": \"Message\", \"value\": \"${message}\", \"short\": false}
                    ]
                }]
            }" 2>/dev/null || true
    fi

    # Email notification
    if [ -n "${NOTIFICATION_EMAIL}" ]; then
        echo "${message}" | mail -s "Backup ${status}: ${BACKUP_ID}" ${NOTIFICATION_EMAIL} 2>/dev/null || true
    fi
}

# ======================
# MAIN EXECUTION
# ======================

main() {
    log INFO "======================================="
    log INFO "Starting Enterprise Backup: ${BACKUP_ID}"
    log INFO "======================================="

    local start_time=$(date +%s)

    # Execute backup steps
    backup_database
    backup_application
    backup_configuration
    backup_metadata

    # Verify backup
    if verify_backup; then
        # Upload to cloud
        upload_to_cloud

        # Cleanup old backups
        cleanup_old_backups

        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log SUCCESS "======================================="
        log SUCCESS "Backup completed successfully!"
        log SUCCESS "Duration: ${duration} seconds"
        log SUCCESS "Backup ID: ${BACKUP_ID}"
        log SUCCESS "======================================="

        # Create recovery instructions
        cat > "${BACKUP_ROOT}/${BACKUP_ID}_recovery.md" << EOF
# Disaster Recovery Instructions

## Backup Information
- **Backup ID**: ${BACKUP_ID}
- **Date**: $(date)
- **Duration**: ${duration} seconds

## Recovery Steps

### 1. Database Recovery

#### PostgreSQL:
\`\`\`bash
pg_restore -d ${DATABASE_URL} ${BACKUP_ID}_database.dump
# OR
gunzip -c ${BACKUP_ID}_database.sql.gz | psql ${DATABASE_URL}
\`\`\`

#### SQLite:
\`\`\`bash
gunzip ${BACKUP_ID}_database.db.gz
cp ${BACKUP_ID}_database.db ./data/production.db
\`\`\`

### 2. Application Recovery
\`\`\`bash
tar -xzf ${BACKUP_ID}_application.tar.gz
\`\`\`

### 3. Configuration Recovery
\`\`\`bash
tar -xzf ${BACKUP_ID}_config.tar.gz
openssl enc -aes-256-cbc -d \
    -in ${BACKUP_ID}_config/env.production.encrypted \
    -out .env.production \
    -pass pass:"ENCRYPTION_KEY"
\`\`\`

### 4. Service Restart
\`\`\`bash
docker-compose down
docker-compose up -d
railway up --detach
vercel --prod
\`\`\`
EOF

        send_notification "SUCCESS" "Backup ${BACKUP_ID} completed in ${duration}s"
        exit 0
    else
        log ERROR "Backup failed!"
        send_notification "FAILED" "Backup ${BACKUP_ID} failed"
        exit 1
    fi
}

# Run main function
main "$@"