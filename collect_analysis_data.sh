#!/bin/bash

# 🔍 УЛУЧШЕННЫЙ ПРОМПТ ДЛЯ ФИНАЛЬНОЙ ПРОВЕРКИ ПРОЕКТА

cd ~/autopilot-core

# Create comprehensive analysis file
cat > final_comprehensive_analysis.txt << 'EOFDATA'
=================================
🚀 AIASSISTANT OS PLATFORM
FINAL COMPREHENSIVE ANALYSIS
=================================
EOFDATA

date >> final_comprehensive_analysis.txt
echo "Project: AIAssistant OS Platform" >> final_comprehensive_analysis.txt
echo "Analyst: AI System Auditor" >> final_comprehensive_analysis.txt
echo "Status: Final Check Before Production" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

# ===================================
# 1. PROJECT STRUCTURE & METRICS
# ===================================
echo "=================================" >> final_comprehensive_analysis.txt
echo "1. PROJECT STRUCTURE & METRICS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== ROOT DIRECTORY ===" >> final_comprehensive_analysis.txt
ls -lah | head -50 >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== PROJECT SIZE ===" >> final_comprehensive_analysis.txt
echo "Total files:" >> final_comprehensive_analysis.txt
find . -type f -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/venv/*" -not -path "*/.git/*" | wc -l >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== BACKEND STRUCTURE ===" >> final_comprehensive_analysis.txt
echo "API Files:" >> final_comprehensive_analysis.txt
ls -lah api/ 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt
echo "Agents Files:" >> final_comprehensive_analysis.txt
ls -lah agents/ 2>/dev/null >> final_comprehensive_analysis.txt

echo "Analysis data collection script created!"


