#!/bin/bash

cd ~/autopilot-core

# Create comprehensive analysis file
cat > final_comprehensive_analysis.txt << 'EOF'
=================================
🚀 AIASSISTANT OS PLATFORM
FINAL COMPREHENSIVE ANALYSIS
=================================
EOF

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

echo "Code files (.py, .tsx, .ts, .jsx, .js):" >> final_comprehensive_analysis.txt
find . -type f \( -name "*.py" -o -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/venv/*" | wc -l >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== BACKEND STRUCTURE ===" >> final_comprehensive_analysis.txt
echo "API Files:" >> final_comprehensive_analysis.txt
ls -lah api/ 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "Agents Files:" >> final_comprehensive_analysis.txt
ls -lah agents/ 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "Backend Line Counts:" >> final_comprehensive_analysis.txt
wc -l api/*.py agents/*.py 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== FRONTEND STRUCTURE ===" >> final_comprehensive_analysis.txt
echo "Web-UI Root:" >> final_comprehensive_analysis.txt
ls -lah web-ui/ 2>/dev/null | head -30 >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "All Pages:" >> final_comprehensive_analysis.txt
find web-ui/app -name "page.tsx" -o -name "layout.tsx" 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "All Components:" >> final_comprehensive_analysis.txt
find web-ui/components -name "*.tsx" -o -name "*.jsx" 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "Frontend Line Counts:" >> final_comprehensive_analysis.txt
find web-ui/app web-ui/components -name "*.tsx" -exec wc -l {} + 2>/dev/null | tail -1 >> final_comprehensive_analysis.txt

# ===================================
# 2. DEPENDENCIES & SECURITY
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "2. DEPENDENCIES & SECURITY" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== FRONTEND PACKAGE.JSON ===" >> final_comprehensive_analysis.txt
cat web-ui/package.json 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== BACKEND REQUIREMENTS.TXT ===" >> final_comprehensive_analysis.txt
cat requirements.txt 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== NPM AUDIT (Frontend Security) ===" >> final_comprehensive_analysis.txt
cd web-ui && npm audit 2>&1 | head -100 >> ../final_comprehensive_analysis.txt
cd ..

echo "" >> final_comprehensive_analysis.txt
echo "=== PIP CHECK (Backend Dependencies) ===" >> final_comprehensive_analysis.txt
if [ -d "venv" ]; then
    source venv/bin/activate
    pip check 2>&1 >> final_comprehensive_analysis.txt
    deactivate
else
    echo "Virtual environment not found" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== NPM OUTDATED (Frontend) ===" >> final_comprehensive_analysis.txt
cd web-ui && npm outdated 2>&1 >> ../final_comprehensive_analysis.txt
cd ..

# ===================================
# 3. CONFIGURATION FILES
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "3. CONFIGURATION FILES" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== NEXT.CONFIG.TS ===" >> final_comprehensive_analysis.txt
cat web-ui/next.config.ts 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== VERCEL.JSON ===" >> final_comprehensive_analysis.txt
if [ -f vercel.json ]; then
    cat vercel.json >> final_comprehensive_analysis.txt
else
    echo "NOT FOUND" >> final_comprehensive_analysis.txt
fi
echo "" >> final_comprehensive_analysis.txt

echo "=== TAILWIND.CONFIG.TS ===" >> final_comprehensive_analysis.txt
cat web-ui/tailwind.config.ts 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== TSCONFIG.JSON ===" >> final_comprehensive_analysis.txt
cat web-ui/tsconfig.json 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== POSTCSS.CONFIG ===" >> final_comprehensive_analysis.txt
cat web-ui/postcss.config.js 2>/dev/null >> final_comprehensive_analysis.txt
cat web-ui/postcss.config.mjs 2>/dev/null >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== ESLINT CONFIG ===" >> final_comprehensive_analysis.txt
cat web-ui/eslint.config.mjs 2>/dev/null >> final_comprehensive_analysis.txt
cat web-ui/.eslintrc.json 2>/dev/null >> final_comprehensive_analysis.txt

# ===================================
# 4. BACKEND CODE DETAILED ANALYSIS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "4. BACKEND CODE DETAILED ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== SERVER.PY ANALYSIS ===" >> final_comprehensive_analysis.txt
if [ -f api/server.py ]; then
    echo "Total Lines:" >> final_comprehensive_analysis.txt
    wc -l api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Imports:" >> final_comprehensive_analysis.txt
    grep "^import\|^from" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "API Endpoints (GET):" >> final_comprehensive_analysis.txt
    grep "@app.get" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "API Endpoints (POST):" >> final_comprehensive_analysis.txt
    grep "@app.post" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "API Endpoints (PUT):" >> final_comprehensive_analysis.txt
    grep "@app.put" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "API Endpoints (DELETE):" >> final_comprehensive_analysis.txt
    grep "@app.delete" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Pydantic Models:" >> final_comprehensive_analysis.txt
    grep "class.*BaseModel" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "CORS Configuration:" >> final_comprehensive_analysis.txt
    grep -A 10 "CORSMiddleware" api/server.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "First 300 lines:" >> final_comprehensive_analysis.txt
    head -300 api/server.py >> final_comprehensive_analysis.txt
else
    echo "SERVER.PY NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== DATABASE.PY ANALYSIS ===" >> final_comprehensive_analysis.txt
if [ -f agents/database.py ]; then
    echo "Total Lines:" >> final_comprehensive_analysis.txt
    wc -l agents/database.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Database Tables (CREATE TABLE statements):" >> final_comprehensive_analysis.txt
    grep -i "CREATE TABLE" agents/database.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Indexes:" >> final_comprehensive_analysis.txt
    grep -i "CREATE INDEX" agents/database.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Class Definitions:" >> final_comprehensive_analysis.txt
    grep "^class " agents/database.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "CRUD Methods:" >> final_comprehensive_analysis.txt
    grep "    def " agents/database.py | head -60 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "SQL Injection Risk Check (raw f-strings):" >> final_comprehensive_analysis.txt
    grep -n "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" agents/database.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "First 250 lines:" >> final_comprehensive_analysis.txt
    head -250 agents/database.py >> final_comprehensive_analysis.txt
else
    echo "DATABASE.PY NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== AI_ROUTER.PY ANALYSIS ===" >> final_comprehensive_analysis.txt
if [ -f agents/ai_router.py ]; then
    echo "Total Lines:" >> final_comprehensive_analysis.txt
    wc -l agents/ai_router.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Available Models Configuration:" >> final_comprehensive_analysis.txt
    grep -A 50 "AVAILABLE_MODELS\|available_models" agents/ai_router.py | head -80 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Classes:" >> final_comprehensive_analysis.txt
    grep "^class " agents/ai_router.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Methods:" >> final_comprehensive_analysis.txt
    grep "    def " agents/ai_router.py >> final_comprehensive_analysis.txt
else
    echo "AI_ROUTER.PY NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== WORKFLOW_ENGINE.PY ANALYSIS ===" >> final_comprehensive_analysis.txt
if [ -f agents/workflow_engine.py ]; then
    echo "✅ WORKFLOW ENGINE EXISTS" >> final_comprehensive_analysis.txt
    wc -l agents/workflow_engine.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Classes:" >> final_comprehensive_analysis.txt
    grep "^class " agents/workflow_engine.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Trigger Types:" >> final_comprehensive_analysis.txt
    grep -i "trigger.*type\|TRIGGER" agents/workflow_engine.py | head -20 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Action Types:" >> final_comprehensive_analysis.txt
    grep -i "action.*type\|ACTION" agents/workflow_engine.py | head -20 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Methods:" >> final_comprehensive_analysis.txt
    grep "    def " agents/workflow_engine.py >> final_comprehensive_analysis.txt
else
    echo "❌ WORKFLOW_ENGINE.PY NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== MCP_CLIENT.PY ANALYSIS ===" >> final_comprehensive_analysis.txt
if [ -f agents/mcp_client.py ]; then
    echo "✅ MCP CLIENT EXISTS" >> final_comprehensive_analysis.txt
    wc -l agents/mcp_client.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Classes:" >> final_comprehensive_analysis.txt
    grep "^class " agents/mcp_client.py >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "OAuth/Integration Methods:" >> final_comprehensive_analysis.txt
    grep -i "oauth\|gmail\|drive\|telegram" agents/mcp_client.py | head -30 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Methods:" >> final_comprehensive_analysis.txt
    grep "    def " agents/mcp_client.py >> final_comprehensive_analysis.txt
else
    echo "❌ MCP_CLIENT.PY NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== OTHER AGENT FILES ===" >> final_comprehensive_analysis.txt
ls -lh agents/ >> final_comprehensive_analysis.txt

# ===================================
# 5. FRONTEND CODE DETAILED ANALYSIS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "5. FRONTEND CODE DETAILED ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== LAYOUT.TSX (Root Layout) ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/layout.tsx ]; then
    wc -l web-ui/app/layout.tsx >> final_comprehensive_analysis.txt
    cat web-ui/app/layout.tsx >> final_comprehensive_analysis.txt
else
    echo "NOT FOUND" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== HOME PAGE (app/page.tsx) ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/page.tsx ]; then
    wc -l web-ui/app/page.tsx >> final_comprehensive_analysis.txt
    head -150 web-ui/app/page.tsx >> final_comprehensive_analysis.txt
else
    echo "NOT FOUND" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== CHAT PAGE ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/chat/page.tsx ]; then
    echo "✅ CHAT PAGE EXISTS" >> final_comprehensive_analysis.txt
    wc -l web-ui/app/chat/page.tsx >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "Imports:" >> final_comprehensive_analysis.txt
    grep "^import" web-ui/app/chat/page.tsx >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "State Management (useState, useEffect):" >> final_comprehensive_analysis.txt
    grep "useState\|useEffect" web-ui/app/chat/page.tsx >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "API Calls (fetch):" >> final_comprehensive_analysis.txt
    grep -n "fetch\|axios" web-ui/app/chat/page.tsx >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    echo "First 120 lines:" >> final_comprehensive_analysis.txt
    head -120 web-ui/app/chat/page.tsx >> final_comprehensive_analysis.txt
else
    echo "❌ CHAT PAGE NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== PROJECTS PAGE ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/projects/page.tsx ]; then
    echo "✅ PROJECTS PAGE EXISTS" >> final_comprehensive_analysis.txt
    wc -l web-ui/app/projects/page.tsx >> final_comprehensive_analysis.txt
    head -100 web-ui/app/projects/page.tsx >> final_comprehensive_analysis.txt
else
    echo "❌ PROJECTS PAGE NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== WORKFLOWS PAGE ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/workflows/page.tsx ]; then
    echo "✅ WORKFLOWS PAGE EXISTS" >> final_comprehensive_analysis.txt
    wc -l web-ui/app/workflows/page.tsx >> final_comprehensive_analysis.txt
    head -100 web-ui/app/workflows/page.tsx >> final_comprehensive_analysis.txt
else
    echo "❌ WORKFLOWS PAGE NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== INTEGRATIONS PAGE ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/integrations/page.tsx ]; then
    echo "✅ INTEGRATIONS PAGE EXISTS" >> final_comprehensive_analysis.txt
    wc -l web-ui/app/integrations/page.tsx >> final_comprehensive_analysis.txt
    head -100 web-ui/app/integrations/page.tsx >> final_comprehensive_analysis.txt
else
    echo "❌ INTEGRATIONS PAGE NOT FOUND!" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== MODELS RANKING PAGE ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/app/models-ranking/page.tsx ]; then
    echo "✅ EXISTS" >> final_comprehensive_analysis.txt
    wc -l web-ui/app/models-ranking/page.tsx >> final_comprehensive_analysis.txt
else
    echo "❌ NOT FOUND" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== COMPONENTS ===" >> final_comprehensive_analysis.txt
if [ -d web-ui/components ]; then
    echo "Available components:" >> final_comprehensive_analysis.txt
    ls -lh web-ui/components/ >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    
    for file in web-ui/components/*.tsx; do
        if [ -f "$file" ]; then
            echo "--- $(basename $file) ---" >> final_comprehensive_analysis.txt
            wc -l "$file" >> final_comprehensive_analysis.txt
        fi
    done
else
    echo "Components directory not found" >> final_comprehensive_analysis.txt
fi

# ===================================
# 6. DATABASE DETAILED ANALYSIS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "6. DATABASE DETAILED ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== DATABASE FILES ===" >> final_comprehensive_analysis.txt
if [ -d data ]; then
    ls -lah data/ >> final_comprehensive_analysis.txt
else
    echo "Data directory not found" >> final_comprehensive_analysis.txt
fi

if [ -f data/history.db ]; then
    echo "" >> final_comprehensive_analysis.txt
    echo "=== DATABASE SCHEMA ===" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db ".schema" >> final_comprehensive_analysis.txt
    
    echo "" >> final_comprehensive_analysis.txt
    echo "=== DATABASE TABLES LIST ===" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;" >> final_comprehensive_analysis.txt
    
    echo "" >> final_comprehensive_analysis.txt
    echo "=== RECORD COUNTS PER TABLE ===" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db "SELECT 'users' as table_name, COUNT(*) as count FROM users UNION ALL SELECT 'projects', COUNT(*) FROM projects UNION ALL SELECT 'databases', COUNT(*) FROM databases UNION ALL SELECT 'database_records', COUNT(*) FROM database_records UNION ALL SELECT 'workflows', COUNT(*) FROM workflows UNION ALL SELECT 'workflow_executions', COUNT(*) FROM workflow_executions UNION ALL SELECT 'requests', COUNT(*) FROM requests UNION ALL SELECT 'chat_sessions', COUNT(*) FROM chat_sessions UNION ALL SELECT 'ai_model_rankings', COUNT(*) FROM ai_model_rankings;" >> final_comprehensive_analysis.txt 2>/dev/null
    
    echo "" >> final_comprehensive_analysis.txt
    echo "=== SAMPLE DATA (First 3 users) ===" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db "SELECT id, email, created_at FROM users LIMIT 3;" >> final_comprehensive_analysis.txt 2>/dev/null
    
    echo "" >> final_comprehensive_analysis.txt
    echo "=== SAMPLE DATA (Recent requests) ===" >> final_comprehensive_analysis.txt
    sqlite3 data/history.db "SELECT id, model, task_type, timestamp FROM requests ORDER BY timestamp DESC LIMIT 5;" >> final_comprehensive_analysis.txt 2>/dev/null
else
    echo "history.db not found!" >> final_comprehensive_analysis.txt
fi

# ===================================
# 7. GIT REPOSITORY ANALYSIS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "7. GIT REPOSITORY ANALYSIS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== CURRENT STATUS ===" >> final_comprehensive_analysis.txt
git status >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt

echo "=== UNCOMMITTED CHANGES SUMMARY ===" >> final_comprehensive_analysis.txt
git diff --stat >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt

echo "=== RECENT COMMITS (30) ===" >> final_comprehensive_analysis.txt
git log --oneline --graph --decorate -30 >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt

echo "=== BRANCH INFO ===" >> final_comprehensive_analysis.txt
git branch -vv >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt

echo "=== REMOTE INFO ===" >> final_comprehensive_analysis.txt
git remote -v >> final_comprehensive_analysis.txt 2>&1
echo "" >> final_comprehensive_analysis.txt

echo "=== GITIGNORE ===" >> final_comprehensive_analysis.txt
cat .gitignore >> final_comprehensive_analysis.txt 2>/dev/null

# ===================================
# 8. DEPLOYMENT STATUS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "8. DEPLOYMENT STATUS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== VERCEL STATUS ===" >> final_comprehensive_analysis.txt
if command -v vercel &> /dev/null; then
    vercel ls 2>&1 | head -20 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    echo "Latest deployment:" >> final_comprehensive_analysis.txt
    vercel ls --json 2>&1 | head -50 >> final_comprehensive_analysis.txt
else
    echo "Vercel CLI not installed" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== RAILWAY STATUS ===" >> final_comprehensive_analysis.txt
if command -v railway &> /dev/null; then
    railway status 2>&1 >> final_comprehensive_analysis.txt
    echo "" >> final_comprehensive_analysis.txt
    railway list 2>&1 >> final_comprehensive_analysis.txt
else
    echo "Railway CLI not installed or not logged in" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== VERCEL PROJECT SETTINGS ===" >> final_comprehensive_analysis.txt
if [ -d .vercel ]; then
    echo "Vercel project linked" >> final_comprehensive_analysis.txt
    cat .vercel/project.json 2>/dev/null >> final_comprehensive_analysis.txt
else
    echo "No Vercel project link found" >> final_comprehensive_analysis.txt
fi

# ===================================
# 9. ENVIRONMENT VARIABLES CHECK
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "9. ENVIRONMENT VARIABLES CHECK" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== ROOT .ENV FILE ===" >> final_comprehensive_analysis.txt
if [ -f .env ]; then
    echo "✅ .env file exists" >> final_comprehensive_analysis.txt
    echo "Environment variables defined (keys only):" >> final_comprehensive_analysis.txt
    grep -v "^#" .env | grep "=" | cut -d'=' -f1 | sort >> final_comprehensive_analysis.txt 2>/dev/null
    echo "" >> final_comprehensive_analysis.txt
    echo "Checking critical variables:" >> final_comprehensive_analysis.txt
    for var in SECRET_KEY GEMINI_API_KEY GROK_API_KEY OPENROUTER_API_KEY; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is set" >> final_comprehensive_analysis.txt
        else
            echo "❌ $var is MISSING" >> final_comprehensive_analysis.txt
        fi
    done
else
    echo "❌ .env file not found" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== .ENV.EXAMPLE (Template) ===" >> final_comprehensive_analysis.txt
if [ -f .env.example ]; then
    cat .env.example >> final_comprehensive_analysis.txt
else
    echo "No .env.example found" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== WEB-UI .ENV.LOCAL ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/.env.local ]; then
    echo "✅ web-ui/.env.local exists" >> final_comprehensive_analysis.txt
    grep -v "^#" web-ui/.env.local | grep "=" | cut -d'=' -f1 >> final_comprehensive_analysis.txt 2>/dev/null
else
    echo "❌ web-ui/.env.local not found" >> final_comprehensive_analysis.txt
fi

# ===================================
# 10. BUILD & TEST STATUS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "10. BUILD & TEST STATUS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== FRONTEND BUILD TEST ===" >> final_comprehensive_analysis.txt
echo "Attempting dry-run build..." >> final_comprehensive_analysis.txt
cd web-ui
npm run build 2>&1 | tail -100 >> ../final_comprehensive_analysis.txt
cd ..

echo "" >> final_comprehensive_analysis.txt
echo "=== TEST FILES ===" >> final_comprehensive_analysis.txt
find . -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" -o -name "test_*.py" 2>/dev/null >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== PYTEST CONFIGURATION ===" >> final_comprehensive_analysis.txt
if [ -f pytest.ini ]; then
    cat pytest.ini >> final_comprehensive_analysis.txt
else
    echo "No pytest.ini found" >> final_comprehensive_analysis.txt
fi

echo "" >> final_comprehensive_analysis.txt
echo "=== JEST CONFIGURATION ===" >> final_comprehensive_analysis.txt
if [ -f web-ui/jest.config.js ]; then
    cat web-ui/jest.config.js >> final_comprehensive_analysis.txt
else
    echo "No Jest config found" >> final_comprehensive_analysis.txt
fi

# ===================================
# 11. DOCUMENTATION STATUS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "11. DOCUMENTATION STATUS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== MARKDOWN FILES ===" >> final_comprehensive_analysis.txt
find . -maxdepth 1 -name "*.md" -exec ls -lh {} \; >> final_comprehensive_analysis.txt 2>/dev/null

echo "" >> final_comprehensive_analysis.txt
echo "=== README.MD (First 150 lines) ===" >> final_comprehensive_analysis.txt
head -150 README.md 2>/dev/null >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "=== API DOCUMENTATION ===" >> final_comprehensive_analysis.txt
echo "FastAPI docs should be at: http://localhost:8000/docs" >> final_comprehensive_analysis.txt
echo "Check if OpenAPI descriptions exist in server.py:" >> final_comprehensive_analysis.txt
grep -n "description=" api/server.py 2>/dev/null | head -20 >> final_comprehensive_analysis.txt

# ===================================
# 12. FINAL STATISTICS
# ===================================
echo "" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "12. FINAL STATISTICS" >> final_comprehensive_analysis.txt
echo "=================================" >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "=== CODE STATISTICS ===" >> final_comprehensive_analysis.txt
echo "Backend Python:" >> final_comprehensive_analysis.txt
find . -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" -exec wc -l {} + 2>/dev/null | tail -1 >> final_comprehensive_analysis.txt
echo "" >> final_comprehensive_analysis.txt

echo "Frontend TypeScript/TSX:" >> final_comprehensive_analysis.txt
find . -name "*.tsx" -o -name "*.ts" | grep -v node_modules | xargs wc -l 2>/dev/null | tail -1 >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "==================================" >> final_comprehensive_analysis.txt
echo "ANALYSIS COMPLETE - $(date)" >> final_comprehensive_analysis.txt
echo "==================================" >> final_comprehensive_analysis.txt

echo "" >> final_comprehensive_analysis.txt
echo "Report size:" >> final_comprehensive_analysis.txt
wc -l final_comprehensive_analysis.txt >> final_comprehensive_analysis.txt

echo ""
echo "✅ Analysis complete! File created: final_comprehensive_analysis.txt"
echo "📊 File size: $(wc -l < final_comprehensive_analysis.txt) lines"
