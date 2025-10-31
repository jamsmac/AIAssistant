#!/bin/bash

# AI Development System - Quick Start Script
# Запускает всю систему автоматически

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$HOME/autopilot-core"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║   🚀 AI Development System - Start       ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка директории
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# 1. Проверка Docker
echo -e "${BLUE}🐳 Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# 2. Запуск Docker контейнеров
echo ""
echo -e "${BLUE}📦 Starting Docker containers...${NC}"
docker-compose up -d

# Ожидание готовности
echo "Waiting for containers to be ready..."
sleep 5

# Проверка статуса
docker-compose ps

echo ""
echo -e "${GREEN}✅ Docker containers started!${NC}"

# 3. Проверка виртуального окружения Python
echo ""
echo -e "${BLUE}🐍 Checking Python environment...${NC}"
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi
echo -e "${GREEN}✅ Python environment ready${NC}"

# 4. Проверка Node modules
echo ""
echo -e "${BLUE}📦 Checking Node.js dependencies...${NC}"
if [ ! -d "$PROJECT_ROOT/web-ui/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found. Installing...${NC}"
    cd "$PROJECT_ROOT/web-ui"
    npm install
    cd "$PROJECT_ROOT"
fi
echo -e "${GREEN}✅ Node.js dependencies ready${NC}"

# 5. Инструкции по запуску сервисов
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ System is ready! Now start the services:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}📍 Terminal 1 - API Server:${NC}"
echo "   cd ~/autopilot-core"
echo "   source venv/bin/activate"
echo "   python api/server.py"
echo ""

echo -e "${YELLOW}📍 Terminal 2 - Web UI:${NC}"
echo "   cd ~/autopilot-core/web-ui"
echo "   npm run dev"
echo ""

echo -e "${YELLOW}📍 Terminal 3 - Telegram Bot (optional):${NC}"
echo "   cd ~/autopilot-core"
echo "   source venv/bin/activate"
echo "   python scripts/telegram_bot.py"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "   • Dashboard:    http://localhost:3000"
echo "   • API Docs:     http://localhost:8000/docs"
echo "   • N8N:          http://localhost:5678"
echo "   • MinIO:        http://localhost:9001"
echo ""

echo -e "${YELLOW}💡 Tip: Use separate terminal windows for each service!${NC}"
echo ""