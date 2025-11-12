#!/bin/bash
# Скрипт для проверки переменных окружения Railway через API

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔍 Проверка переменных окружения Railway${NC}\n"

# Проверка Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI не установлен${NC}"
    echo "Установите: npm install -g @railway/cli"
    exit 1
fi

# Получение информации о проекте
echo -e "${YELLOW}📋 Информация о проекте:${NC}"
railway status 2>&1 || echo "Не удалось получить статус"
echo ""

# Попытка получить список переменных через разные методы
echo -e "${YELLOW}🔑 Попытка получить переменные окружения...${NC}\n"

# Метод 1: Через railway variables (если сервис привязан)
if railway variables 2>&1 | grep -q "No service linked"; then
    echo -e "${YELLOW}⚠️  Сервис не привязан. Используйте один из методов ниже:${NC}\n"
    
    echo "Метод 1: Через Railway Dashboard (Рекомендуется)"
    echo "  1. Откройте: https://railway.app/dashboard"
    echo "  2. Выберите проект 'AIAssistant'"
    echo "  3. Перейдите в Variables tab"
    echo "  4. Проверьте наличие следующих переменных:"
    echo ""
    echo "     ✅ CORS_ORIGINS"
    echo "     ✅ FRONTEND_URL"
    echo "     ✅ ENVIRONMENT"
    echo ""
    
    echo "Метод 2: Привязать сервис через CLI"
    echo "  1. Запустите: railway service"
    echo "  2. Выберите нужный сервис"
    echo "  3. Затем запустите: railway variables"
    echo ""
    
    echo "Метод 3: Проверка через Railway API"
    echo "  URL: https://railway.app/dashboard"
    echo "  Проект: AIAssistant"
    echo ""
else
    echo -e "${GREEN}✅ Переменные окружения:${NC}"
    railway variables 2>&1 | head -50
fi

# Проверка критических переменных
echo ""
echo -e "${YELLOW}📝 Критические переменные для проверки:${NC}"
echo ""
echo "Обязательные:"
echo "  ✅ CORS_ORIGINS - Должен содержать Vercel URL"
echo "  ✅ FRONTEND_URL - Должен содержать Vercel URL"
echo "  ✅ ENVIRONMENT - Должен быть 'production'"
echo "  ✅ SECRET_KEY - Должен быть минимум 64 символа"
echo ""
echo "API Keys (должны быть настроены):"
echo "  ✅ OPENAI_API_KEY"
echo "  ✅ ANTHROPIC_API_KEY"
echo "  ✅ GEMINI_API_KEY (или GOOGLE_AI_API_KEY)"
echo "  ✅ OPENROUTER_API_KEY"
echo ""

# Проверка через API health check
RAILWAY_URL="https://aiassistant-production-7a4d.up.railway.app"
echo -e "${YELLOW}🏥 Проверка API через health check...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/health" || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ API работает (HTTP $response)${NC}"
    echo ""
    echo "Детали health check:"
    curl -s "$RAILWAY_URL/api/health" | jq '.' 2>/dev/null || curl -s "$RAILWAY_URL/api/health"
else
    echo -e "${RED}❌ API не отвечает (HTTP $response)${NC}"
fi

echo ""
echo -e "${YELLOW}💡 Для обновления переменных используйте:${NC}"
echo "  ./scripts/update_railway_vars.sh"
echo ""
echo "Или вручную:"
echo "  railway variables set CORS_ORIGINS=\"https://your-app.vercel.app\""
echo "  railway variables set FRONTEND_URL=\"https://your-app.vercel.app\""








