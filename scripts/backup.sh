#!/bin/bash

# AI Development System - Backup Script
# Создает резервную копию всей системы

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_ROOT="$HOME/autopilot-core"
BACKUP_DIR="$HOME/autopilot-backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo -e "${BLUE}🔄 Starting backup process...${NC}"
echo "Backup location: $BACKUP_PATH"

# Создание директории для backup
mkdir -p "$BACKUP_PATH"

# 1. Backup конфигурационных файлов
echo -e "${GREEN}📄 Backing up configuration files...${NC}"
cp "$PROJECT_ROOT/.env" "$BACKUP_PATH/.env.backup"
cp "$PROJECT_ROOT/docker-compose.yml" "$BACKUP_PATH/"
cp "$PROJECT_ROOT/requirements.txt" "$BACKUP_PATH/"
cp "$PROJECT_ROOT/README.md" "$BACKUP_PATH/"

# 2. Backup Python кода
echo -e "${GREEN}🐍 Backing up Python code...${NC}"
mkdir -p "$BACKUP_PATH/agents"
mkdir -p "$BACKUP_PATH/api"
mkdir -p "$BACKUP_PATH/scripts"
cp -r "$PROJECT_ROOT/agents/"*.py "$BACKUP_PATH/agents/" 2>/dev/null || true
cp -r "$PROJECT_ROOT/api/"*.py "$BACKUP_PATH/api/" 2>/dev/null || true
cp -r "$PROJECT_ROOT/scripts/"*.py "$BACKUP_PATH/scripts/" 2>/dev/null || true
cp "$PROJECT_ROOT/scripts/backup.sh" "$BACKUP_PATH/scripts/" 2>/dev/null || true

# 3. Backup Next.js проекта (только важные файлы)
echo -e "${GREEN}⚛️ Backing up Next.js project...${NC}"
mkdir -p "$BACKUP_PATH/web-ui"
cp "$PROJECT_ROOT/web-ui/package.json" "$BACKUP_PATH/web-ui/"
cp "$PROJECT_ROOT/web-ui/package-lock.json" "$BACKUP_PATH/web-ui/" 2>/dev/null || true
cp "$PROJECT_ROOT/web-ui/next.config.ts" "$BACKUP_PATH/web-ui/" 2>/dev/null || true
cp "$PROJECT_ROOT/web-ui/tailwind.config.ts" "$BACKUP_PATH/web-ui/" 2>/dev/null || true
cp "$PROJECT_ROOT/web-ui/tsconfig.json" "$BACKUP_PATH/web-ui/" 2>/dev/null || true

# Backup Next.js app directory
mkdir -p "$BACKUP_PATH/web-ui/app"
cp -r "$PROJECT_ROOT/web-ui/app" "$BACKUP_PATH/web-ui/" 2>/dev/null || true

# 4. Backup PostgreSQL database
echo -e "${GREEN}🗄️ Backing up PostgreSQL database...${NC}"
if docker ps | grep -q autopilot_postgres; then
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
        pg_dumpall -U autopilot > "$BACKUP_PATH/postgres_dump.sql"
    echo "✅ PostgreSQL backup completed"
else
    echo "⚠️ PostgreSQL container not running, skipping database backup"
fi

# 5. Backup Docker volumes (опционально)
echo -e "${GREEN}🐳 Backing up Docker volumes info...${NC}"
docker volume ls > "$BACKUP_PATH/docker_volumes.txt"

# 6. Создание информационного файла
echo -e "${GREEN}📝 Creating backup info...${NC}"
cat > "$BACKUP_PATH/BACKUP_INFO.txt" << EOF
AI Development System Backup
============================
Backup Date: $(date)
Backup Name: $BACKUP_NAME

Contents:
- Configuration files (.env, docker-compose.yml, requirements.txt)
- Python code (agents, api, scripts)
- Next.js project (app, configs)
- PostgreSQL database dump
- Docker volumes information

To restore:
1. Copy files back to $PROJECT_ROOT
2. Restore PostgreSQL: cat postgres_dump.sql | docker-compose exec -T postgres psql -U autopilot
3. Run: docker-compose up -d
4. Run: cd web-ui && npm install && npm run dev
5. Run: source venv/bin/activate && python api/server.py

System Info:
- Python version: $(python --version 2>&1)
- Node version: $(node --version 2>&1)
- Docker version: $(docker --version 2>&1)
EOF

# 7. Создание архива
echo -e "${GREEN}📦 Creating archive...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

# Удаление временной папки
rm -rf "$BACKUP_PATH"

# 8. Статистика
ARCHIVE_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
echo ""
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📁 Archive: ${BACKUP_NAME}.tar.gz"
echo -e "📊 Size: $ARCHIVE_SIZE"
echo -e "📂 Location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 9. Очистка старых backup'ов (оставляем последние 5)
echo -e "${BLUE}🧹 Cleaning old backups (keeping last 5)...${NC}"
cd "$BACKUP_DIR"
ls -t backup_*.tar.gz | tail -n +6 | xargs -r rm
echo "Remaining backups:"
ls -lh backup_*.tar.gz 2>/dev/null || echo "No backups found"

echo ""
echo -e "${GREEN}🎉 All done!${NC}"