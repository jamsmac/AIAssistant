#!/usr/bin/env python3
"""
Скрипт для автоматического обновления рейтингов AI моделей
Запускается по расписанию (cron/systemd timer)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Добавляем путь к agents
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from ranking_collector import RankingCollector
from database import get_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rankings_update.log'),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)


def send_telegram_notification(message: str):
    """
    Отправить уведомление в Telegram
    (опционально, если настроен Telegram Bot)
    """
    try:
        import requests
        import os

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            logger.info("Telegram credentials not found, skipping notification")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent")
        else:
            logger.warning(f"⚠️ Telegram notification failed: {response.status_code}")

    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")


def check_for_new_leaders(db, new_stats: dict) -> list:
    """
    Проверить появились ли новые лидеры в категориях
    
    Returns:
        Список сообщений о новых лидерах
    """
    notifications = []
    categories = ['reasoning', 'coding', 'vision', 'chat', 'agents', 'translation', 'local']

    for category in categories:
        current_rankings = db.get_rankings_by_category(category, limit=1)
        if current_rankings:
            leader = current_rankings[0]
            notifications.append(
                f"🏆 *{category.upper()}* leader: {leader['model_name']} (score: {leader['score']})"
            )

    return notifications


def main():
    """Главная функция обновления"""
    logger.info("="*60)
    logger.info("🚀 Starting AI Models Rankings Update")
    logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    try:
        collector = RankingCollector()
        db = get_db()

        logger.info("\n📊 Collecting rankings from sources...")
        stats = collector.collect_all_rankings()

        total = sum(stats.values())
        logger.info(f"\n✅ Collection complete:")
        logger.info(f"   Total models updated: {total}")
        for category, count in stats.items():
            logger.info(f"   - {category}: {count} models")

        logger.info("\n🔍 Checking for new leaders...")
        leaders = check_for_new_leaders(db, stats)

        notification_message = f"""
🤖 *AI Models Rankings Updated*

✅ Updated: {total} models across {len(stats)} categories

📊 *Current Leaders:*
{chr(10).join(leaders)}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        logger.info("\n📱 Sending notification...")
        send_telegram_notification(notification_message)

        logger.info("\n" + "="*60)
        logger.info("✅ Update completed successfully!")
        logger.info("="*60 + "\n")
        return 0

    except Exception as e:
        error_msg = f"❌ Error during update: {e}"
        logger.error(error_msg)
        send_telegram_notification(f"⚠️ Rankings update failed:\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())




















