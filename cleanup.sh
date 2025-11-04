#!/bin/bash

echo "🧹 Cleaning up project files..."
echo "================================"
echo ""

# Файлы с секретами
echo "🔴 Removing files with secrets..."
rm -f ADD_MISSING_7.txt
rm -f ALL_18_VARIABLES.txt
rm -f COPY_TO_RAILWAY.txt
echo "✅ Secret files removed"
echo ""

# Дубликаты
echo "🟡 Removing duplicate files..."
rm -f RAILWAY_FINAL.md
rm -f FINAL_RAILWAY_SETUP.md
rm -f QUICK_ADD_VARIABLES.md
rm -f ИНСТРУКЦИЯ_ДОБАВИТЬ_ВСЕ.md
echo "✅ Duplicates removed"
echo ""

# Устаревшие файлы
echo "🟡 Removing outdated files..."
rm -f COPY_PASTE_COMMANDS.txt
rm -f CONTINUE_DEPLOY.md
rm -f DEPLOY_VIA_GIT.md
rm -f deploy_railway_v2.sh
rm -f COMPLETION_REPORT.md
rm -f FINAL_SUMMARY.md
rm -f STATUS.md
rm -f VERCEL_SIZE_FIX.md
echo "✅ Outdated files removed"
echo ""

# Подсчёт оставшихся файлов
echo "📊 Files remaining:"
echo "   Markdown: $(ls *.md 2>/dev/null | wc -l)"
echo "   Scripts: $(ls *.sh 2>/dev/null | wc -l)"
echo "   Text: $(ls *.txt 2>/dev/null | wc -l)"
echo ""

echo "================================"
echo "✅ Cleanup completed!"
echo ""
echo "Remaining documentation:"
ls *.md 2>/dev/null | sort
