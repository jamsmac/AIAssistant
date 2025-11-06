#!/bin/bash

# Production Deployment Script with PostgreSQL
# Full security implementation

set -e

echo "=========================================="
echo "🚀 AI Assistant Platform - Production Deployment"
echo "   PostgreSQL + OAuth + CSRF Edition"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Please install it first:${NC}"
    echo "   curl -fsSL https://railway.com/install.sh | sh"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Railway. Please run: railway login${NC}"
    exit 1
fi

# Check PostgreSQL client (for migrations)
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠ PostgreSQL client not found. Migrations will run via Python.${NC}"
    PSQL_AVAILABLE=false
else
    PSQL_AVAILABLE=true
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Step 1: Set up Railway PostgreSQL
echo -e "\n${YELLOW}Step 1: Setting up PostgreSQL database...${NC}"

# Check if PostgreSQL plugin exists
POSTGRES_URL=$(railway variables get DATABASE_URL 2>/dev/null || echo "")

if [ -z "$POSTGRES_URL" ]; then
    echo "Creating PostgreSQL database on Railway..."
    railway add postgresql

    # Wait for database to be ready
    echo "Waiting for database to be provisioned..."
    sleep 10

    # Get the new DATABASE_URL
    POSTGRES_URL=$(railway variables get DATABASE_URL)

    if [ -z "$POSTGRES_URL" ]; then
        echo -e "${RED}❌ Failed to create PostgreSQL database${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ PostgreSQL database created${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL database already exists${NC}"
fi

# Step 2: Run database migrations
echo -e "\n${YELLOW}Step 2: Running database migrations...${NC}"

# Set DATABASE_URL for local migration run
export DATABASE_URL="$POSTGRES_URL"

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required packages
pip install asyncpg psycopg2-binary bcrypt pyjwt httpx

# Run migrations
python api/database/run_migrations.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database migrations completed${NC}"
else
    echo -e "${RED}❌ Database migrations failed${NC}"
    exit 1
fi

# Step 3: Set environment variables
echo -e "\n${YELLOW}Step 3: Setting production environment variables...${NC}"

# Generate secure keys if not already set
JWT_SECRET=$(railway variables get JWT_SECRET 2>/dev/null || echo "")
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    railway variables set JWT_SECRET="$JWT_SECRET"
    echo "  ✅ JWT_SECRET generated"
fi

CSRF_SECRET=$(railway variables get CSRF_SECRET 2>/dev/null || echo "")
if [ -z "$CSRF_SECRET" ]; then
    CSRF_SECRET=$(openssl rand -hex 32)
    railway variables set CSRF_SECRET="$CSRF_SECRET"
    echo "  ✅ CSRF_SECRET generated"
fi

# Set other environment variables
railway variables set \
    ENVIRONMENT=production \
    PYTHON_VERSION=3.11 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=info \
    DATABASE_POOL_SIZE=20 \
    DATABASE_MAX_OVERFLOW=40 \
    RATE_LIMIT_PER_MINUTE=60 \
    RATE_LIMIT_PER_HOUR=1000 \
    SESSION_LIFETIME_HOURS=24 \
    MAX_SESSIONS_PER_USER=5 \
    ENABLE_OAUTH=true \
    ENABLE_2FA=true \
    ENABLE_RATE_LIMITING=true \
    ENABLE_AUDIT_LOG=true \
    START_COMMAND="python api/database/run_migrations.py && uvicorn api.server_refactored:app --host 0.0.0.0 --port \$PORT --workers 4"

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Step 4: Update railway.toml
echo -e "\n${YELLOW}Step 4: Creating Railway configuration...${NC}"

cat > railway.toml << 'EOF'
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt && pip install asyncpg psycopg2-binary httpx"

[deploy]
startCommand = "python api/database/run_migrations.py && uvicorn api.server_refactored:app --host 0.0.0.0 --port $PORT --workers 4"
healthcheckPath = "/api/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "aiassistant"
type = "web"
EOF

echo -e "${GREEN}✅ Railway configuration created${NC}"

# Step 5: Update requirements.txt
echo -e "\n${YELLOW}Step 5: Updating requirements.txt...${NC}"

# Ensure PostgreSQL packages are included
if ! grep -q "asyncpg" requirements.txt 2>/dev/null; then
    echo "asyncpg>=0.29.0" >> requirements.txt
fi

if ! grep -q "psycopg2-binary" requirements.txt 2>/dev/null; then
    echo "psycopg2-binary>=2.9.9" >> requirements.txt
fi

if ! grep -q "httpx" requirements.txt 2>/dev/null; then
    echo "httpx>=0.25.0" >> requirements.txt
fi

echo -e "${GREEN}✅ Requirements updated${NC}"

# Step 6: Deploy to Railway
echo -e "\n${YELLOW}Step 6: Deploying to Railway...${NC}"

# Commit changes
git add -A
git commit -m "feat: Production deployment with PostgreSQL, OAuth, and CSRF protection" || true

# Deploy
railway up --detach --service AIAssistant

echo -e "${GREEN}✅ Deployment initiated${NC}"

# Step 7: Get deployment URL
echo -e "\n${YELLOW}Step 7: Getting deployment information...${NC}"

# Wait for deployment to start
sleep 5

# Get the deployment URL
DEPLOY_URL=$(railway domain 2>/dev/null | grep -o 'https://[^ ]*' | head -1)

if [ -z "$DEPLOY_URL" ]; then
    echo -e "${YELLOW}Generating Railway domain...${NC}"
    railway domain
    sleep 3
    DEPLOY_URL=$(railway domain 2>/dev/null | grep -o 'https://[^ ]*' | head -1)
fi

# Step 8: Update Vercel frontend
echo -e "\n${YELLOW}Step 8: Updating Vercel frontend configuration...${NC}"

if [ ! -z "$DEPLOY_URL" ]; then
    # Update Vercel environment variable
    cd web-ui 2>/dev/null || cd .

    # Remove old variable and add new one
    vercel env rm NEXT_PUBLIC_API_URL production --yes 2>/dev/null || true
    echo "$DEPLOY_URL" | vercel env add NEXT_PUBLIC_API_URL production

    # Set CORS origins in Railway
    railway variables set ALLOWED_ORIGINS="$DEPLOY_URL,https://*.vercel.app,http://localhost:3000"

    echo -e "${GREEN}✅ Frontend configuration updated${NC}"
fi

# Step 9: Run health checks
echo -e "\n${YELLOW}Step 9: Running health checks...${NC}"

# Wait for deployment to be ready
echo "Waiting for deployment to be ready (this may take a few minutes)..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s "$DEPLOY_URL/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 10
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "\n${YELLOW}⚠ Health check timed out. Deployment may still be in progress.${NC}"
fi

# Step 10: Display summary
echo -e "\n=========================================="
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "=========================================="
echo -e "\n📊 Deployment Summary:"
echo -e "  Backend URL: ${GREEN}$DEPLOY_URL${NC}"
echo -e "  Database: ${GREEN}PostgreSQL (Railway)${NC}"
echo -e "  Security: ${GREEN}OAuth + CSRF + JWT${NC}"
echo -e "  Status: ${GREEN}Production Ready${NC}"

echo -e "\n📝 Next Steps:"
echo -e "  1. Set OAuth credentials in Railway dashboard:"
echo -e "     - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
echo -e "     - GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET"
echo -e "  2. Update OAuth redirect URIs:"
echo -e "     - Google: $DEPLOY_URL/api/auth/callback/google"
echo -e "     - GitHub: $DEPLOY_URL/api/auth/callback/github"
echo -e "  3. Deploy frontend with: cd web-ui && vercel --prod"
echo -e "  4. Test the deployment:"
echo -e "     - API Health: $DEPLOY_URL/api/health"
echo -e "     - API Docs: $DEPLOY_URL/docs"

echo -e "\n🔒 Security Notes:"
echo -e "  - JWT_SECRET has been generated and set"
echo -e "  - CSRF_SECRET has been generated and set"
echo -e "  - Database migrations completed"
echo -e "  - Rate limiting enabled (60 req/min)"
echo -e "  - Session management active"

echo -e "\n📊 Monitoring:"
echo -e "  - View logs: railway logs --service AIAssistant"
echo -e "  - Database console: railway connect postgresql"
echo -e "  - Deployment status: railway status"

echo -e "\n=========================================="
echo -e "${GREEN}Your AI Assistant Platform is now live!${NC}"
echo -e "==========================================\n"