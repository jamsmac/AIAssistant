#!/bin/bash

# AI Development System - Restore Script
# Восстанавливает систему из резервной копии

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Конфигурация
PROJECT_ROOT="$HOME/autopilot-core"
BACKUP_DIR="$HOME/autopilot-backups"

echo -e "${BLUE}🔄 AI Development System - Restore${NC}"
echo ""

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Available backups:"
    echo ""
    ls -lh "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || echo "No backups found"
    echo ""
    echo "Usage: ./restore.sh <backup_name.tar.gz>"
    echo "Example: ./restore.sh backup_20251029_040000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

# Проверка существования backup
if [ ! -f "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_PATH${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will overwrite current files!${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

# Создание временной директории
TEMP_DIR=$(mktemp -d)
echo -e "${GREEN}📦 Extracting backup...${NC}"
tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"

# Получаем имя папки внутри архива
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
EXTRACT_PATH="$TEMP_DIR/$BACKUP_NAME"

# 1. Показываем информацию о backup
if [ -f "$EXTRACT_PATH/BACKUP_INFO.txt" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    cat "$EXTRACT_PATH/BACKUP_INFO.txt"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
fi

# 2. Создание backup текущего состояния
echo -e "${YELLOW}💾 Creating backup of current state...${NC}"
SAFETY_BACKUP="$HOME/autopilot-backups/before_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
cd "$PROJECT_ROOT/.."
tar -czf "$SAFETY_BACKUP" autopilot-core 2>/dev/null || echo "⚠️ Could not create safety backup"
echo "Safety backup: $SAFETY_BACKUP"

# 3. Остановка сервисов
echo -e "${BLUE}🛑 Stopping services...${NC}"
cd "$PROJECT_ROOT"
docker-compose down 2>/dev/null || true
pkill -f "python api/server.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "telegram_bot.py" 2>/dev/null || true
sleep 2

# 4. Восстановление конфигов
echo -e "${GREEN}📄 Restoring configuration files...${NC}"
cp "$EXTRACT_PATH/.env.backup" "$PROJECT_ROOT/.env"
cp "$EXTRACT_PATH/docker-compose.yml" "$PROJECT_ROOT/"
cp "$EXTRACT_PATH/requirements.txt" "$PROJECT_ROOT/"
[ -f "$EXTRACT_PATH/README.md" ] && cp "$EXTRACT_PATH/README.md" "$PROJECT_ROOT/"

# 5. Восстановление Python кода
echo -e "${GREEN}🐍 Restoring Python code...${NC}"
[ -d "$EXTRACT_PATH/agents" ] && cp -r "$EXTRACT_PATH/agents/"* "$PROJECT_ROOT/agents/"
[ -d "$EXTRACT_PATH/api" ] && cp -r "$EXTRACT_PATH/api/"* "$PROJECT_ROOT/api/"
[ -d "$EXTRACT_PATH/scripts" ] && cp -r "$EXTRACT_PATH/scripts/"* "$PROJECT_ROOT/scripts/"

# 6. Восстановление Next.js
echo -e "${GREEN}⚛️ Restoring Next.js project...${NC}"
if [ -d "$EXTRACT_PATH/web-ui" ]; then
    cp "$EXTRACT_PATH/web-ui/package.json" "$PROJECT_ROOT/web-ui/"
    [ -f "$EXTRACT_PATH/web-ui/package-lock.json" ] && cp "$EXTRACT_PATH/web-ui/package-lock.json" "$PROJECT_ROOT/web-ui/"
    [ -f "$EXTRACT_PATH/web-ui/next.config.ts" ] && cp "$EXTRACT_PATH/web-ui/next.config.ts" "$PROJECT_ROOT/web-ui/"
    [ -f "$EXTRACT_PATH/web-ui/tailwind.config.ts" ] && cp "$EXTRACT_PATH/web-ui/tailwind.config.ts" "$PROJECT_ROOT/web-ui/"
    [ -d "$EXTRACT_PATH/web-ui/app" ] && cp -r "$EXTRACT_PATH/web-ui/app" "$PROJECT_ROOT/web-ui/"
fi

# 7. Запуск Docker
echo -e "${GREEN}🐳 Starting Docker containers...${NC}"
cd "$PROJECT_ROOT"
docker-compose up -d
sleep 5

# 8. Восстановление PostgreSQL
if [ -f "$EXTRACT_PATH/postgres_dump.sql" ]; then
    echo -e "${GREEN}🗄️ Restoring PostgreSQL database...${NC}"
    cat "$EXTRACT_PATH/postgres_dump.sql" | docker-compose exec -T postgres psql -U autopilot
    echo "✅ Database restored"
else
    echo "⚠️ No PostgreSQL dump found, skipping database restore"
fi

# 9. Переустановка зависимостей
echo -e "${GREEN}📦 Installing dependencies...${NC}"

# Python
echo "Installing Python packages..."
cd "$PROJECT_ROOT"
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -r requirements.txt --break-system-packages -q

# Node.js
echo "Installing Node.js packages..."
cd "$PROJECT_ROOT/web-ui"
npm install --silent

# 10. Очистка
rm -rf "$TEMP_DIR"

# 11. Финальный статус
echo ""
echo -e "${GREEN}✅ Restore completed successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Start API Server:"
echo "   cd $PROJECT_ROOT"
echo "   source venv/bin/activate"
echo "   python api/server.py"
echo ""
echo "2️⃣  Start Web UI (new terminal):"
echo "   cd $PROJECT_ROOT/web-ui"
echo "   npm run dev"
echo ""
echo "3️⃣  Start Telegram Bot (optional, new terminal):"
echo "   cd $PROJECT_ROOT"
echo "   source venv/bin/activate"
echo "   python scripts/telegram_bot.py"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""