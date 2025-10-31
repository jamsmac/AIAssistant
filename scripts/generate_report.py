#!/usr/bin/env python3
"""
Генератор аналитического отчета по использованию AI моделей
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / "agents"))

from database import get_db


def print_section(title: str):
    """Красивый заголовок секции"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def generate_report(days: int = 7):
    """Генерировать отчет"""
    
    db = get_db()
    analytics = db.get_performance_analytics(days=days)
    
    print("\n" + "🤖 AI MODELS PERFORMANCE REPORT".center(60))
    print(f"Period: Last {days} days".center(60))
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(60))
    
    # Общая статистика
    print_section("📊 SUMMARY")
    summary = analytics['summary']
    print(f"  Total Requests:  {summary['total_requests']:,}")
    print(f"  Total Tokens:    {summary['total_tokens']:,}")
    print(f"  Total Cost:      ${summary['total_cost']:.4f}")
    print(f"  Unique Models:   {summary['unique_models']}")
    print(f"  Unique Tasks:    {summary['unique_tasks']}")
    
    # Статистика по моделям
    print_section("🎯 MODELS PERFORMANCE")
    print(f"  {'Model':<30} {'Requests':<10} {'Success':<10} {'Tokens':<12} {'Cost':<10}")
    print("  " + "-"*72)
    
    for model in analytics['models'][:10]:
        print(f"  {model['model']:<30} "
              f"{model['total_requests']:<10} "
              f"{model['success_rate']:<9.1f}% "
              f"{model['total_tokens']:>11,} "
              f"${model['total_cost']:>8.4f}")
    
    # Статистика по задачам
    print_section("📋 TASK TYPES")
    print(f"  {'Task Type':<20} {'Count':<10} {'Avg Tokens':<15} {'Total Cost':<10}")
    print("  " + "-"*55)
    
    for task in analytics['tasks']:
        task_type = task['task_type'] or 'unknown'
        print(f"  {task_type:<20} "
              f"{task['count']:<10} "
              f"{task['avg_tokens']:>14,.1f} "
              f"${task['total_cost']:>8.4f}")
    
    # Распределение по времени
    print_section("⏰ HOURLY DISTRIBUTION")
    hourly = analytics['hourly_distribution']
    if hourly:
        max_requests = max(h['requests_count'] for h in hourly)
        for hour_data in hourly:
            hour = hour_data['hour']
            count = hour_data['requests_count']
            bar_length = int((count / max_requests) * 40)
            bar = "█" * bar_length
            print(f"  {hour}:00  {bar} {count}")
    
    # Самые дорогие запросы
    print_section("💰 TOP EXPENSIVE REQUESTS")
    for idx, req in enumerate(analytics['expensive_requests'][:5], 1):
        prompt_preview = req['prompt'][:50] + "..." if len(req['prompt']) > 50 else req['prompt']
        print(f"\n  #{idx} ${req['cost']:.4f} - {req['model']}")
        print(f"      {prompt_preview}")
        print(f"      Tokens: {req['tokens']:,} | {req['timestamp']}")
    
    # Кэш статистика
    print_section("💾 CACHE STATISTICS")
    cache_stats = db.get_cache_stats()
    print(f"  Total Entries:         {cache_stats['total_entries']}")
    print(f"  Total Uses:            {cache_stats['total_uses']}")
    print(f"  Avg Uses per Entry:    {cache_stats['avg_uses_per_entry']:.1f}")
    
    if cache_stats['top_cached']:
        print("\n  Top Cached Queries:")
        for idx, cached in enumerate(cache_stats['top_cached'][:5], 1):
            prompt_preview = cached['prompt'][:45] + "..." if len(cached['prompt']) > 45 else cached['prompt']
            print(f"    #{idx} {prompt_preview}")
            print(f"        Uses: {cached['use_count']} | Model: {cached['model']}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate AI models performance report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    
    args = parser.parse_args()
    generate_report(args.days)