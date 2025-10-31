#!/bin/bash

# AI Development System - Stop Script
# Останавливает все сервисы системы

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$HOME/autopilot-core"

echo -e "${RED}"
echo "╔═══════════════════════════════════════════╗"
echo "║   🛑 AI Development System - Stop        ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

cd "$PROJECT_ROOT"

# 1. Остановка Python процессов
echo -e "${YELLOW}🐍 Stopping Python services...${NC}"
pkill -f "python api/server.py" 2>/dev/null && echo "  ✓ API Server stopped" || echo "  ℹ API Server not running"
pkill -f "python scripts/telegram_bot.py" 2>/dev/null && echo "  ✓ Telegram Bot stopped" || echo "  ℹ Telegram Bot not running"

# 2. Остановка Node.js процессов
echo ""
echo -e "${YELLOW}⚛️  Stopping Node.js services...${NC}"
pkill -f "next dev" 2>/dev/null && echo "  ✓ Next.js dev server stopped" || echo "  ℹ Next.js not running"
pkill -f "npm run dev" 2>/dev/null || true

# 3. Остановка Docker контейнеров
echo ""
echo -e "${YELLOW}🐳 Stopping Docker containers...${NC}"
docker-compose down

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"
echo ""
echo -e "${BLUE}📊 System status:${NC}"
echo "  • Docker containers: stopped"
echo "  • API Server: stopped"
echo "  • Web UI: stopped"
echo "  • Telegram Bot: stopped"
echo ""
echo -e "${YELLOW}💡 To start again, run: ./start.sh${NC}"
echo ""