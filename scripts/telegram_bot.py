"""
Telegram Bot для AI Development System
Команды: /start, /chat, /stats, /models, /create, /help
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка .env из корня проекта
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "http://localhost:8000"

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in .env file!")
    sys.exit(1)

# ============================================
# Команды бота
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_message = """
🤖 *AI Development System Bot*

Доступные команды:

/chat <вопрос> - Задать вопрос AI
/stats - Статистика использования
/models - Список доступных моделей
/create <идея> - Создать проект
/help - Справка

Просто напиши сообщение для быстрого чата с AI!
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📚 *Справка по командам:*

**/chat <вопрос>**
Отправить запрос к AI
Пример: `/chat Write Python function to sort array`

**/stats**
Показать статистику использования системы

**/models**
Список всех AI моделей и их статус

**/create <идея>**
Создать полный проект из идеи
Пример: `/create Todo app with FastAPI`

*Быстрый режим:*
Просто напиши сообщение без команды - бот отправит его в AI Chat!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/api/stats")
            response.raise_for_status()
            data = response.json()
        
        stats_text = f"""
📊 *Статистика системы*

📞 Всего запросов: {data['calls']}
🎯 Использовано токенов: {data['tokens']:,}
💰 Общая стоимость: ${data['cost']:.6f}
📈 Средняя стоимость: ${data['avg_cost_per_call']:.6f}

🤖 *Активные модели:* {sum(data['available_models'].values())}/5
        """
        
        if data['by_model']:
            stats_text += "\n\n*Использование по моделям:*\n"
            for model, info in data['by_model'].items():
                stats_text += f"\n`{model}`\n"
                stats_text += f"  • Запросов: {info['calls']}\n"
                stats_text += f"  • Токенов: {info['tokens']:,}\n"
                stats_text += f"  • Стоимость: ${info['cost']:.6f}\n"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/api/models")
            response.raise_for_status()
            data = response.json()
        
        models_text = "🤖 *Доступные AI модели:*\n\n"
        
        for model_key, info in data.items():
            status = "✅" if info['available'] else "❌"
            models_text += f"{status} *{info['name']}*\n"
            models_text += f"   Стоимость: {info['cost']}\n"
            models_text += f"   Лучше для: {', '.join(info['use_cases'][:3])}\n\n"
        
        await update.message.reply_text(models_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /chat"""
    if not context.args:
        await update.message.reply_text("❌ Использование: /chat <ваш вопрос>")
        return
    
    prompt = ' '.join(context.args)
    await send_to_ai(update, prompt, task_type='code', budget='cheap')

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /create"""
    if not context.args:
        await update.message.reply_text("❌ Использование: /create <идея проекта>")
        return
    
    idea = ' '.join(context.args)
    
    # Отправка "думает..."
    status_msg = await update.message.reply_text("🔄 Создаю проект... Это займет ~30 секунд...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_URL}/api/project",
                json={"idea": idea, "budget": "medium"}
            )
            response.raise_for_status()
            data = response.json()
        
        result_text = f"""
✅ *Проект создан!*

🆔 Project ID: `{data['project_id']}`
💰 Total Cost: ${data['total_cost']:.6f}

📐 *Architecture:*
Model: {data['architecture']['model']}

💻 *Code Generated:*
Model: {data['code']['model']}

🔍 *Review:*
Model: {data['review']['model']}

Проект готов! Стоимость: ${data['total_cost']:.6f}
        """
        
        await status_msg.edit_text(result_text, parse_mode='Markdown')
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при создании проекта: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    prompt = update.message.text
    await send_to_ai(update, prompt, task_type='code', budget='cheap')

async def send_to_ai(update: Update, prompt: str, task_type: str = 'code', budget: str = 'cheap'):
    """Отправка запроса к AI"""
    # Показываем что думает
    status_msg = await update.message.reply_text("🤔 AI думает...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/api/chat",
                json={
                    "prompt": prompt,
                    "task_type": task_type,
                    "complexity": 5,
                    "budget": budget
                }
            )
            response.raise_for_status()
            data = response.json()
        
        if data.get('error'):
            await status_msg.edit_text(f"❌ Ошибка: {data['response']}")
            return
        
        # Формируем ответ
        result = data['response']
        footer = f"\n\n_Model: {data['model']} | Cost: ${data['cost']:.6f} | Tokens: {data['tokens']}_"
        
        # Telegram лимит 4096 символов
        max_length = 4000
        if len(result) > max_length:
            result = result[:max_length] + "...\n\n[Ответ обрезан из-за ограничения Telegram]"
        
        await status_msg.edit_text(result + footer, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        await status_msg.edit_text(f"❌ Ошибка API: {str(e)}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")

# ============================================
# Главная функция
# ============================================

def main():
    """Запуск бота"""
    logger.info("🚀 Starting Telegram Bot...")
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("models", models_command))
    application.add_handler(CommandHandler("chat", chat_command))
    application.add_handler(CommandHandler("create", create_command))
    
    # Обработчик обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("✅ Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()