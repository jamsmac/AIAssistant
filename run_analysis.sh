#!/bin/bash

echo "Starting comprehensive analysis..."

# Create analysis file
cat > final_comprehensive_analysis.txt << 'HEADER'
=================================
🚀 AIASSISTANT OS PLATFORM
FINAL COMPREHENSIVE ANALYSIS
=================================
HEADER

date >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

# 1. Project Structure
echo "=================================" >> final_comprehensive_analysis.txt
echo "1. PROJECT STRUCTURE & METRICS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== ROOT DIRECTORY ===" >> final_comprehensive_analysis.txt
ls -la | head -30 >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== PROJECT SIZE ===" >> final_comprehensive_analysis.txt
echo "Total files:" >> final_comprehensive_analysis.txt
find . -type f -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/venv/*" -not -path "*/.git/*" 2>/dev/null | wc -l >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== BACKEND STRUCTURE ===" >> final_comprehensive_analysis.txt
ls -la api/ 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt
ls -la agents/ 2>/dev/null | head -20 >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== FRONTEND STRUCTURE ===" >> final_comprehensive_analysis.txt
ls -la web-ui/ 2>/dev/null | head -20 >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "All Pages:" >> final_comprehensive_analysis.txt
find web-ui/app -name "page.tsx" 2>/dev/null >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "All Components:" >> final_comprehensive_analysis.txt
find web-ui/components -name "*.tsx" 2>/dev/null >> final_comprehensive_analysis.txt

# 2. Dependencies
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "2. DEPENDENCIES" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== BACKEND REQUIREMENTS ===" >> final_comprehensive_analysis.txt
cat requirements.txt 2>/dev/null >> final_comprehensive_analysis.txt

# 3. Backend Analysis
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "3. BACKEND ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== API ENDPOINTS ===" >> final_comprehensive_analysis.txt
if [ -f api/server.py ]; then
    echo "GET endpoints:" >> final_comprehensive_analysis.txt
    grep "@app.get\|@router.get" api/server.py 2>/dev/null >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    echo "POST endpoints:" >> final_comprehensive_analysis.txt
    grep "@app.post\|@router.post" api/server.py 2>/dev/null >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    echo "Routers included:" >> final_comprehensive_analysis.txt
    grep "app.include_router" api/server.py 2>/dev/null >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== DATABASE TABLES ===" >> final_comprehensive_analysis.txt
if [ -f agents/database.py ]; then
    grep -i "CREATE TABLE" agents/database.py 2>/dev/null >> final_comprehensive_analysis.txt
fi

# 4. Frontend Analysis
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "4. FRONTEND ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== PAGES ===" >> final_comprehensive_analysis.txt
for page in web-ui/app/*/page.tsx web-ui/app/page.tsx; do
    if [ -f "$page" ]; then
        echo "$page exists ✅" >> final_comprehensive_analysis.txt
    fi
done

# 5. Database
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "5. DATABASE" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

if [ -f data/history.db ]; then
    echo "Database exists ✅" >> final_comprehensive_analysis.txt
    echo "Tables:" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db "SELECT name FROM sqlite_master WHERE type='table';" 2>/dev/null >> final_comprehensive_analysis.txt
else
    echo "Database not found ❌" >> final_comprehensive_analysis.txt
fi

# 6. Git Status
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "6. GIT STATUS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

git status --short >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt
echo "Recent commits:" >> final_comprehensive_analysis.txt
git log --oneline -5 >> final_comprehensive_analysis.txt 2>&1

# 7. Environment
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "7. ENVIRONMENT" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

if [ -f .env ]; then
    echo ".env exists ✅" >> final_comprehensive_analysis.txt
    echo "Variables defined:" >> final_comprehensive_analysis.txt
    grep -v "^#" .env | grep "=" | cut -d'=' -f1 2>/dev/null >> final_comprehensive_analysis.txt
else
    echo ".env not found ❌" >> final_comprehensive_analysis.txt
fi

# 8. Documentation
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "8. DOCUMENTATION" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

ls -la *.md 2>/dev/null >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "Analysis complete!" >> final_comprehensive_analysis.txt

cat final_comprehensive_analysis.txt
