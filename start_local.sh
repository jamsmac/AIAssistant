#!/bin/bash
# Запуск backend и frontend для локальной разработки

set -e

echo "🚀 Запуск локальной разработки..."
echo ""

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено."
    echo "   Создайте его: python3 -m venv venv"
    exit 1
fi

# Проверка .env
if [ ! -f ".env" ]; then
    echo "❌ .env файл не найден."
    echo "   Скопируйте .env.example в .env и настройте его"
    exit 1
fi

# Проверка ENVIRONMENT
if grep -q "ENVIRONMENT=production" .env 2>/dev/null; then
    echo "⚠️  ВНИМАНИЕ: ENVIRONMENT=production в .env!"
    echo "   Для локальной разработки должно быть ENVIRONMENT=development"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Создать директории
mkdir -p data logs

# Проверка frontend .env.local
if [ ! -f "web-ui/.env.local" ]; then
    echo "📝 Создание web-ui/.env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > web-ui/.env.local
fi

# Функция очистки при выходе
cleanup() {
    echo ""
    echo "🛑 Остановка процессов..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    pkill -f "python api/server.py" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Запуск backend
echo "📦 Запуск backend на http://localhost:8000..."
source venv/bin/activate
python api/server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Ждем запуск backend
echo "   Ожидание запуска backend..."
sleep 5

# Проверка что backend запустился
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ Backend не запустился. Проверьте logs/backend.log"
    exit 1
fi

echo "   ✅ Backend запущен"

# Запуск frontend
echo "🎨 Запуск frontend на http://localhost:3000..."
cd web-ui
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Ждем запуск frontend
echo "   Ожидание запуска frontend..."
sleep 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Локальная разработка запущена!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Логи:"
echo "   - Backend:  logs/backend.log"
echo "   - Frontend: logs/frontend.log"
echo ""
echo "   Для остановки нажмите Ctrl+C"
echo ""

# Ожидание сигнала
wait

