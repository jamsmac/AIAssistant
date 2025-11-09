# 🔄 Data Recovery & Backup Guide

**Last Updated**: November 9, 2025
**For**: Railway Production Deployment
**Critical**: Data persistence configuration

---

## 📋 Overview

This guide covers:
- Railway volume configuration for persistent data
- Automated backup procedures
- Data recovery steps
- Disaster recovery planning

---

## 🛡️ Railway Persistent Storage

### Volume Configuration

**File**: `railway.toml`

```toml
[[deploy.volumes]]
mountPath = "/app/data"
name = "data-volume"
```

**What This Does**:
- Creates persistent storage volume on Railway
- Mounts volume at `/app/data` in container
- Data survives across deploys and restarts
- Stores `history.db` and `autopilot_cache.db`

### Verifying Volume Mount

After deployment, check volume status:

```bash
# Via Railway CLI
railway volume list

# Expected output:
# NAME          MOUNT PATH    SIZE
# data-volume   /app/data     1 GB
```

### Database Files Location

```
/app/data/
├── history.db          # Main user database
├── autopilot_cache.db  # Cache database
└── backups/           # Automated backups
    ├── history_20251109_120000.db
    └── autopilot_cache_20251109_120000.db
```

---

## 💾 Automated Backup System

### Backup Script

**Location**: `scripts/backup_db.sh`

**What It Does**:
1. Creates timestamped backups of all databases
2. Verifies backup integrity with SQLite PRAGMA check
3. Retains last 7 days of backups
4. Optional: Uploads to S3 (if configured)
5. Generates backup report

### Running Backups Manually

```bash
# On Railway
railway run bash scripts/backup_db.sh

# Locally
./scripts/backup_db.sh
```

### Scheduling Automated Backups

**Option A: Railway Cron (Recommended)**

Add to `railway.toml`:

```toml
[deploy.cron]
  [deploy.cron.backup]
    schedule = "0 2 * * *"  # Daily at 2 AM UTC
    command = "bash scripts/backup_db.sh"
```

**Option B: APScheduler (In-App)**

Add to `api/server.py` startup:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler.add_job(
    func=run_backup_script,
    trigger="cron",
    hour=2,  # 2 AM UTC
    minute=0,
    id="daily_backup"
)
```

### Environment Variables

```bash
# Optional S3 upload
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=your-backup-bucket

# Backup configuration
BACKUP_DIR=/app/data/backups
RETENTION_DAYS=7

# Optional webhook notification
BACKUP_WEBHOOK_URL=https://your-webhook-url.com
```

---

## 🚨 Data Recovery Procedures

### Scenario 1: Accidental Data Delete

**Symptoms**:
- User data missing
- Records disappeared
- Workflows deleted

**Recovery Steps**:

1. **Stop Application** (prevents further changes)
   ```bash
   railway down
   ```

2. **List Available Backups**
   ```bash
   railway run ls -lh /app/data/backups
   ```

3. **Identify Correct Backup**
   - Find backup before incident
   - Check timestamp in filename
   - Example: `history_20251109_140000.db`

4. **Restore Database**
   ```bash
   # Copy backup to main database
   railway run cp /app/data/backups/history_20251109_140000.db /app/data/history.db

   # Verify integrity
   railway run sqlite3 /app/data/history.db "PRAGMA integrity_check;"
   # Should output: ok
   ```

5. **Restart Application**
   ```bash
   railway up
   ```

6. **Verify Data Restored**
   - Login to application
   - Check user accounts exist
   - Verify workflows present

---

### Scenario 2: Database Corruption

**Symptoms**:
- "database disk image is malformed"
- Application crashes on startup
- SQLite errors in logs

**Recovery Steps**:

1. **Confirm Corruption**
   ```bash
   railway run sqlite3 /app/data/history.db "PRAGMA integrity_check;"
   # If corrupted, shows errors instead of "ok"
   ```

2. **Attempt Repair** (try this first)
   ```bash
   # Dump database to SQL
   railway run sqlite3 /app/data/history.db ".dump" > dump.sql

   # Create new database from dump
   railway run sqlite3 /app/data/history_new.db < dump.sql

   # Backup old database
   railway run mv /app/data/history.db /app/data/history_corrupted.db

   # Replace with repaired version
   railway run mv /app/data/history_new.db /app/data/history.db
   ```

3. **If Repair Fails, Restore from Backup**
   - Follow Scenario 1 steps
   - Use most recent valid backup

---

### Scenario 3: Complete Data Loss (Railway Volume Deleted)

**Symptoms**:
- Empty database
- All users gone
- Fresh installation state

**Recovery Steps**:

1. **Check if S3 Backups Available**
   ```bash
   aws s3 ls s3://your-backup-bucket/backups/
   ```

2. **Download Latest Backup from S3**
   ```bash
   # Download to local machine
   aws s3 cp s3://your-backup-bucket/backups/history_20251109_140000.db ./history.db

   # Upload to Railway volume
   railway volume upload data-volume ./history.db /app/data/history.db
   ```

3. **If No S3 Backups Available**
   - **CRITICAL**: This is complete data loss
   - You will need to restore from local backups if available
   - Or start with empty database

4. **Prevent Future Losses**
   - ✅ Ensure volume configuration in railway.toml
   - ✅ Enable S3 backup uploads
   - ✅ Test recovery procedure monthly

---

## 🧪 Testing Recovery (Monthly)

**Recovery Drill Checklist**:

1. **Test Backup Creation**
   ```bash
   railway run bash scripts/backup_db.sh
   # Verify: Backup created successfully
   ```

2. **Test Backup Download**
   ```bash
   railway volume download data-volume /app/data/backups/history_*.db ./test_backup.db
   # Verify: File downloaded successfully
   ```

3. **Test Integrity Check**
   ```bash
   sqlite3 ./test_backup.db "PRAGMA integrity_check;"
   # Verify: Returns "ok"
   ```

4. **Test S3 Upload** (if configured)
   ```bash
   aws s3 ls s3://your-backup-bucket/backups/ | tail -n 5
   # Verify: Recent backups present
   ```

5. **Document Test Results**
   - Date tested: _______
   - Result: Pass/Fail
   - Issues found: _______
   - Actions taken: _______

---

## 📊 Backup Monitoring

### Daily Checks

**Automated** (via webhook):
- Backup script sends success/failure notification
- Check webhook endpoint for daily backup reports

**Manual Verification**:
```bash
# Check last backup date
railway run ls -lt /app/data/backups | head -n 5

# Verify backup size (should be >100KB for history.db)
railway run du -h /app/data/backups/*.db
```

### Alert Configuration

Add to monitoring system:

```python
# In api/server.py or monitoring script
from datetime import datetime, timedelta

def check_backup_status():
    latest_backup = get_latest_backup_time()
    if datetime.utcnow() - latest_backup > timedelta(hours=26):
        alert_manager.send_alert(
            severity="HIGH",
            message="Database backup is overdue (>24 hours)",
            details={"last_backup": latest_backup}
        )
```

---

## 🔐 Backup Security

### Encryption at Rest

**Railway Volumes**:
- Encrypted by default ✅
- No additional configuration needed

**S3 Backups**:
```bash
# Enable server-side encryption
aws s3 cp backup.db s3://bucket/backup.db --sse AES256

# Or use customer-managed keys
aws s3 cp backup.db s3://bucket/backup.db --sse aws:kms --sse-kms-key-id your-key-id
```

### Access Control

**Railway**:
- Only team members with Railway access can download volumes
- Use Railway RBAC to limit access

**S3**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:user/backup-user"
      },
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::bucket/backups/*"
    }
  ]
}
```

---

## 📈 Monitoring Metrics

Track these metrics:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Backup Age** | <24 hours | >26 hours |
| **Backup Size** | >100KB | <50KB (likely empty) |
| **Backup Success Rate** | 100% | <95% (7 days) |
| **Volume Usage** | <80% | >90% |
| **Recovery Test Age** | <30 days | >45 days |

---

## 🚀 Migration to PostgreSQL (Future)

**When to Migrate**:
- Database >1GB
- Need better concurrency
- Multiple read replicas required
- Advanced features (full-text search, JSON queries)

**Migration Steps** (high-level):

1. **Export from SQLite**
   ```bash
   sqlite3 history.db .dump > export.sql
   ```

2. **Convert SQL Syntax**
   - Use pgloader or manual conversion
   - Handle SQLite-specific syntax

3. **Import to PostgreSQL**
   ```bash
   psql -h railway.app -d database -f export.sql
   ```

4. **Update Application**
   ```python
   # Change from
   DATABASE_URL = "sqlite:///data/history.db"

   # To
   DATABASE_URL = os.getenv("DATABASE_URL")  # Railway provides this
   ```

5. **Test Thoroughly**
   - All CRUD operations
   - Migrations
   - Performance

---

## 📞 Emergency Contacts

**Data Loss Emergency**:
1. Stop application immediately
2. Contact Railway support: support@railway.app
3. Contact team lead: [YOUR_EMAIL]
4. Do NOT make any changes until recovery plan confirmed

**Backup Issues**:
- Check Railway logs: `railway logs`
- Review backup script output
- Verify S3 credentials (if using S3)

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] Railway volume configured in railway.toml
- [ ] Backup script tested and working
- [ ] S3 credentials configured (optional but recommended)
- [ ] Cron job scheduled for daily backups
- [ ] Recovery procedure tested successfully
- [ ] Monitoring alerts configured
- [ ] Team trained on recovery procedures
- [ ] Emergency contacts documented

---

## 📚 Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Full deployment guide
- [QUICK_START.md](../QUICK_START.md) - Getting started
- [AUDIT_CROSS_CHECK_REPORT.md](../AUDIT_CROSS_CHECK_REPORT.md) - Security audit

---

**Created**: November 9, 2025
**Purpose**: Data persistence and recovery for Railway deployment
**Status**: Ready for Production

---

END OF DATA RECOVERY GUIDE
