# 🧹 План Очистки Проекта

## 🔴 УДАЛИТЬ (содержат секреты или дубликаты)

### Файлы с API ключами:
```bash
rm ADD_MISSING_7.txt
rm ALL_18_VARIABLES.txt
rm COPY_TO_RAILWAY.txt
```

### Дубликаты документации:
```bash
rm RAILWAY_FINAL.md  # дубликат README_RAILWAY.md
rm FINAL_RAILWAY_SETUP.md  # информация есть в других файлах
rm QUICK_ADD_VARIABLES.md  # информация в RAILWAY_VARIABLES.md
rm ИНСТРУКЦИЯ_ДОБАВИТЬ_ВСЕ.md  # дубликат на русском
```

### Устаревшие файлы:
```bash
rm COPY_PASTE_COMMANDS.txt  # старые команды
rm CONTINUE_DEPLOY.md  # устаревший
rm DEPLOY_VIA_GIT.md  # устаревший метод
rm deploy_railway_v2.sh  # старая версия
rm COMPLETION_REPORT.md  # старый отчёт
rm FINAL_SUMMARY.md  # старая сводка
rm STATUS.md  # устаревший статус
rm VERCEL_SIZE_FIX.md  # решённая проблема
```

---

## 🟢 ОСТАВИТЬ (актуальная документация)

### Основная документация:
- ✅ `README.md` - главный README
- ✅ `README_RAILWAY.md` - Railway deployment guide
- ✅ `SECURITY_CHECK.md` - security audit report

### Railway:
- ✅ `RAILWAY_DEPLOY_STEPS.md` - пошаговая инструкция
- ✅ `RAILWAY_TEST_RESULTS.md` - результаты тестов
- ✅ `RAILWAY_VARIABLES.md` - настройка переменных (БЕЗ реальных ключей)
- ✅ `deploy_railway.sh` - deploy скрипт

### Vercel:
- ✅ `VERCEL_SETUP.md` - setup guide
- ✅ `VERCEL_DEPLOYMENT_SUMMARY.md` - deployment summary
- ✅ `QUICK_VERCEL_DEPLOY.md` - quick start
- ✅ `deploy_vercel.sh` - deploy скрипт

### Troubleshooting:
- ✅ `TROUBLESHOOTING.md` - решение проблем
- ✅ `CHEATSHEET.md` - cheat sheet

### Quick Guides:
- ✅ `QUICKSTART.md` - quick start guide
- ✅ `DEPLOY_QUICK.md` - quick deploy
- ✅ `DEPLOY.md` - full deploy guide
- ✅ `PROMPTS.md` - AI prompts

### Features:
- ✅ `CHAT_SIDEBAR_FEATURE.md` - chat sidebar feature
- ✅ `FILE_UPLOAD_FEATURE.md` - file upload feature
- ✅ `NEW_TABLES_SUMMARY.md` - new tables documentation

### Scripts:
- ✅ `start.sh` - start script
- ✅ `stop.sh` - stop script
- ✅ `requirements.txt` - Python dependencies

---

## ⚠️ ТРЕБУЮТ ОБНОВЛЕНИЯ (удалить реальные ключи)

### Заменить реальные ключи на плейсхолдеры:
- ⚠️ `add_railway_variables.sh` - заменить ключи на `<YOUR_KEY_HERE>`
- ⚠️ `RAILWAY_VARIABLES.md` - использовать примеры вместо реальных ключей

---

## 🔧 Команды для Очистки

```bash
# Удалить файлы с секретами
rm ADD_MISSING_7.txt ALL_18_VARIABLES.txt COPY_TO_RAILWAY.txt

# Удалить дубликаты
rm RAILWAY_FINAL.md FINAL_RAILWAY_SETUP.md QUICK_ADD_VARIABLES.md ИНСТРУКЦИЯ_ДОБАВИТЬ_ВСЕ.md

# Удалить устаревшие
rm COPY_PASTE_COMMANDS.txt CONTINUE_DEPLOY.md DEPLOY_VIA_GIT.md
rm deploy_railway_v2.sh COMPLETION_REPORT.md FINAL_SUMMARY.md
rm STATUS.md VERCEL_SIZE_FIX.md

# Проверить что осталось
ls *.md *.txt *.sh | wc -l
```

---

## ✅ После Очистки

Должно остаться примерно 20-25 файлов документации:
- README файлы (2)
- Railway документация (4)
- Vercel документация (4)
- Guides (5)
- Features (3)
- Scripts (4)
- Other (2-3)

---

**Выполнить очистку:** `bash cleanup.sh`
