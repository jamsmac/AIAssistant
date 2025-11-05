# 🔒 SECURITY CLEANUP GUIDE

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Очистка секретов из Git истории

### 🚨 Проблема
В Git истории остались файлы с секретными данными (.env файлы), которые могут быть скомпрометированы.

### ✅ Шаги по очистке

#### Шаг 1: Создайте backup
```bash
cp -r ~/autopilot-core ~/autopilot-core-backup
```

#### Шаг 2: Установите BFG Repo-Cleaner (рекомендуется)
```bash
# macOS
brew install bfg

# Или скачайте JAR файл
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
```

#### Шаг 3: Очистите историю с помощью BFG
```bash
cd ~/autopilot-core

# Удалите все .env файлы из истории
bfg --delete-files .env --no-blob-protection
bfg --delete-files .env.local --no-blob-protection

# Или используя JAR
java -jar bfg.jar --delete-files .env --no-blob-protection
```

#### Шаг 4: Альтернативный метод через git filter-branch
```bash
# Если BFG недоступен, используйте git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch web-ui/.env.local" \
  --prune-empty --tag-name-filter cat -- --all
```

#### Шаг 5: Очистите рефлоги и сборщик мусора
```bash
# Удалите рефлоги
git reflog expire --expire=now --all

# Запустите сборщик мусора
git gc --prune=now --aggressive
```

#### Шаг 6: Force push изменения (ОСТОРОЖНО!)
```bash
# ВНИМАНИЕ: Это перезапишет удаленную историю
git push --force --all
git push --force --tags
```

### 🔑 Генерация новых секретов

#### Генерация SECRET_KEY для JWT:
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

#### Генерация NEXTAUTH_SECRET:
```bash
openssl rand -base64 32
```

### 📝 Создание .env файла (НЕ коммитить!)

Создайте новый `.env` файл:
```bash
cat > .env << 'EOF'
# Сгенерируйте новый ключ командой выше
SECRET_KEY=your-new-secret-key-here

# API ключи (получите новые)
ANTHROPIC_API_KEY=new-key
OPENAI_API_KEY=new-key
GEMINI_API_KEY=new-key
GROK_API_KEY=new-key
OPENROUTER_API_KEY=new-key

# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Server
HOST=0.0.0.0
PORT=8000
EOF
```

### 🛡️ Проверка результатов

#### Проверьте, что секреты удалены из истории:
```bash
# Поиск .env файлов в истории
git log --all --full-history -- "*/.env*"

# Должно вернуть пустой результат
```

#### Проверьте размер репозитория:
```bash
du -sh .git
# Размер должен уменьшиться
```

### ⚡ Quick Commands (все в одной команде)

```bash
# Backup + Clean + GC
cp -r . ../backup && \
bfg --delete-files '.env*' --no-blob-protection && \
git reflog expire --expire=now --all && \
git gc --prune=now --aggressive
```

### 🔐 Финальные рекомендации

1. **Немедленно ротируйте ВСЕ ключи:**
   - API ключи всех сервисов
   - Пароли базы данных
   - JWT секреты
   - OAuth credentials

2. **Настройте секретный менеджер:**
   - Используйте переменные окружения
   - Или HashiCorp Vault
   - Или AWS Secrets Manager

3. **Добавьте pre-commit hooks:**
```bash
# Создайте .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
# Проверка на .env файлы
if git diff --cached --name-only | grep -E '\.env'; then
  echo "ERROR: Trying to commit .env file!"
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

4. **Мониторинг:**
   - Настройте GitHub secret scanning
   - Используйте tools like TruffleHog
   - Регулярно аудируйте коммиты

### ❓ Troubleshooting

**Проблема:** `fatal: bad revision 'rm'`
**Решение:** Используйте BFG вместо filter-branch

**Проблема:** Push rejected после очистки
**Решение:** Используйте `--force` флаг (убедитесь, что у вас есть backup!)

**Проблема:** Секреты все еще видны на GitHub
**Решение:** Контактируйте GitHub support для полной очистки кеша

### 📞 Контакты для помощи

- GitHub Support: https://support.github.com/
- Security team: security@your-company.com

---

**Последнее обновление:** Ноябрь 2025
**Статус:** ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ВЫПОЛНЕНИЕ