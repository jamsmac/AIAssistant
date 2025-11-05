# 🚀 Quick Setup Guide - Запуск за 5 минут

## 1. Supabase Setup (База данных)

### Вариант A: Новый проект (Рекомендуется)
1. Перейдите на https://supabase.com
2. Создайте новый проект (бесплатно)
3. Получите ключи:
   - Settings → API → Copy `URL` and `anon public` key
   - Settings → Database → Copy connection string

### Вариант B: Используйте существующий проект
```bash
# Вы уже инициализировали Supabase
cd web-ui
npx supabase link --project-ref your-project-ref
npx supabase db push
```

## 2. Настройка переменных окружения

```bash
# Откройте файл для редактирования
nano web-ui/.env.production.local

# Заполните ОБЯЗАТЕЛЬНЫЕ поля:
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# Сгенерируйте секрет для NextAuth:
openssl rand -base64 32
# Вставьте результат в NEXTAUTH_SECRET=
```

## 3. Перезапуск с новыми настройками

```bash
# Остановите сервер (Ctrl+C)
# Затем запустите снова:
cd web-ui
npm run build && npm start
```

## 4. Проверка работы

Откройте в браузере:
- http://localhost:3000 - Главная страница
- http://localhost:3000/login - Вход в систему
- http://localhost:3000/register - Регистрация
- http://localhost:3000/api/health - Статус системы

## 5. Доступные страницы для просмотра

### Публичные страницы (работают без БД):
✅ http://localhost:3000/ - Landing page
✅ http://localhost:3000/models-ranking - AI Models Ranking
✅ http://localhost:3000/blog - Blog (без данных)
✅ http://localhost:3000/agents - FractalAgents Dashboard

### Админ панели (визуальный интерфейс работает):
✅ http://localhost:3000/admin/monitoring - System Monitoring
✅ http://localhost:3000/admin/analytics - Advanced Analytics
✅ http://localhost:3000/admin/blog - Blog Management

### Функциональные страницы:
✅ http://localhost:3000/chat - AI Chat Interface
✅ http://localhost:3000/workflows - Workflow Builder
✅ http://localhost:3000/projects - Projects Dashboard
✅ http://localhost:3000/integrations - Integrations

## Проблемы и решения

### Ошибка "Database error: Invalid API key"
→ Нужно заполнить Supabase ключи в .env.production.local

### Ошибка "Invalid Sentry Dsn"
→ Это не критично, можно игнорировать или добавить реальный Sentry DSN

### Страница не загружается
→ Проверьте что сервер запущен: `npm start` в папке web-ui

## Deployment на Vercel (1 клик)

```bash
# Из папки web-ui:
npx vercel --prod

# Следуйте инструкциям
# Добавьте env переменные в Vercel Dashboard
```

## Что работает без настройки БД:
- ✅ Все UI компоненты
- ✅ Навигация
- ✅ Статические страницы
- ✅ Monitoring Dashboard
- ✅ Analytics Dashboard
- ✅ Models Ranking
- ✅ Agent Network Visualization

---

**Приложение готово к использованию!** 🎉

Откройте http://localhost:3000 и исследуйте интерфейс.