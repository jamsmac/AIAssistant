#!/bin/bash
# Скрипт для настройки автоматического обновления рейтингов

echo "🔧 Setting up AI Rankings Scheduler"
echo ""

# Путь к проекту
PROJECT_DIR="$HOME/autopilot-core"
SCRIPT_PATH="$PROJECT_DIR/scripts/update_rankings.py"
VENV_PATH="$PROJECT_DIR/venv"

# Проверка существования файлов
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

echo "📁 Project directory: $PROJECT_DIR"
echo "🐍 Python script: $SCRIPT_PATH"
echo ""

# Создаем cron job для еженедельного запуска (каждый понедельник в 9:00)
CRON_COMMAND="0 9 * * 1 cd $PROJECT_DIR && source $VENV_PATH/bin/activate && python $SCRIPT_PATH"

echo "⏰ Cron schedule: Every Monday at 9:00 AM"
echo "📝 Cron command:"
echo "   $CRON_COMMAND"
echo ""

# Добавляем в crontab
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "📋 Current crontab:"
crontab -l
echo ""
echo "💡 To view logs: tail -f $PROJECT_DIR/rankings_update.log"
echo "💡 To remove: crontab -e (delete the line)"




















