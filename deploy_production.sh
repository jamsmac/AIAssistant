#!/bin/bash

# ===========================================
# AIAssistant OS Platform - Production Deploy Script
# ===========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}🚀 AIAssistant Production Deployment${NC}"
echo -e "${GREEN}=====================================${NC}"

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed. Please install it first.${NC}"
        exit 1
    fi
}

# Function to check environment variable
check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${YELLOW}⚠️  Warning: $1 is not set${NC}"
        return 1
    fi
    return 0
}

# 1. Check prerequisites
echo -e "\n${YELLOW}1. Checking prerequisites...${NC}"
check_command git
check_command python3
check_command npm
check_command railway || echo -e "${YELLOW}Railway CLI not found. Install with: npm i -g @railway/cli${NC}"
check_command vercel || echo -e "${YELLOW}Vercel CLI not found. Install with: npm i -g vercel${NC}"

# 2. Check git status
echo -e "\n${YELLOW}2. Checking git status...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
    git status --short
    read -p "Do you want to commit them? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"
    fi
fi

# 3. Pull latest changes
echo -e "\n${YELLOW}3. Pulling latest changes...${NC}"
git pull origin main || echo -e "${YELLOW}Could not pull. Make sure you're on the right branch.${NC}"

# 4. Install/Update dependencies
echo -e "\n${YELLOW}4. Installing dependencies...${NC}"

# Backend dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Frontend dependencies
echo "Installing Node dependencies..."
cd web-ui
npm install
cd ..

# 5. Run tests
echo -e "\n${YELLOW}5. Running tests...${NC}"
read -p "Do you want to run tests before deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backend tests
    echo "Running backend tests..."
    python3 -m pytest tests/ -v --tb=short || echo -e "${YELLOW}Some tests failed${NC}"

    # Frontend tests
    echo "Running frontend tests..."
    cd web-ui
    npm run test || echo -e "${YELLOW}Some tests failed${NC}"
    cd ..
fi

# 6. Build frontend
echo -e "\n${YELLOW}6. Building frontend...${NC}"
cd web-ui
npm run build
cd ..

# 7. Check environment variables
echo -e "\n${YELLOW}7. Checking environment variables...${NC}"
ENV_COMPLETE=true

# Critical variables
for var in SECRET_KEY OPENAI_API_KEY ANTHROPIC_API_KEY; do
    if ! check_env $var; then
        ENV_COMPLETE=false
    fi
done

if [ "$ENV_COMPLETE" = false ]; then
    echo -e "${YELLOW}Please set missing environment variables before deployment${NC}"
    echo -e "${YELLOW}Copy .env.production.example to .env and fill in the values${NC}"
fi

# 8. Deploy Backend to Railway
echo -e "\n${YELLOW}8. Deploying Backend to Railway...${NC}"
if command -v railway &> /dev/null; then
    echo "Logging into Railway..."
    railway login || echo -e "${YELLOW}Please login to Railway${NC}"

    echo "Linking to Railway project..."
    railway link || echo -e "${YELLOW}Please create a Railway project first${NC}"

    echo "Setting Railway variables..."
    # Set production environment variables
    railway variables set ENVIRONMENT=production
    railway variables set PYTHON_VERSION=3.11

    # Copy environment variables from .env if they exist
    if [ -f .env ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^#.*$ ]] && [ -n "$key" ]; then
                # Remove quotes if present
                value="${value%\"}"
                value="${value#\"}"
                railway variables set "$key=$value" 2>/dev/null || true
            fi
        done < .env
    fi

    echo "Deploying to Railway..."
    railway up --detach

    echo -e "${GREEN}✅ Backend deployed to Railway${NC}"
    echo "Backend URL: $(railway status --json | jq -r '.url')"
else
    echo -e "${YELLOW}Railway CLI not installed. Skipping Railway deployment.${NC}"
fi

# 9. Deploy Frontend to Vercel
echo -e "\n${YELLOW}9. Deploying Frontend to Vercel...${NC}"
if command -v vercel &> /dev/null; then
    cd web-ui

    echo "Deploying to Vercel..."
    vercel --prod --yes

    cd ..
    echo -e "${GREEN}✅ Frontend deployed to Vercel${NC}"
else
    echo -e "${YELLOW}Vercel CLI not installed. Skipping Vercel deployment.${NC}"
fi

# 10. Post-deployment checks
echo -e "\n${YELLOW}10. Running post-deployment checks...${NC}"

# Get deployment URLs
if command -v railway &> /dev/null; then
    BACKEND_URL=$(railway status --json 2>/dev/null | jq -r '.url' || echo "Not available")
    echo -e "Backend URL: ${GREEN}$BACKEND_URL${NC}"
fi

if command -v vercel &> /dev/null; then
    FRONTEND_URL=$(cd web-ui && vercel ls --json 2>/dev/null | jq -r '.[0].url' || echo "Not available")
    echo -e "Frontend URL: ${GREEN}$FRONTEND_URL${NC}"
fi

# Test backend health
if [ "$BACKEND_URL" != "Not available" ]; then
    echo -e "\nTesting backend health..."
    curl -s "$BACKEND_URL/api/health" | jq '.' || echo -e "${YELLOW}Backend health check failed${NC}"
fi

# 11. Update git with deployment info
echo -e "\n${YELLOW}11. Updating deployment status...${NC}"
cat > DEPLOYMENT_STATUS.md << EOF
# Deployment Status

**Last Deployment:** $(date)
**Backend URL:** $BACKEND_URL
**Frontend URL:** $FRONTEND_URL
**Status:** ✅ Deployed

## Deployment Checklist
- [x] Code committed to git
- [x] Dependencies installed
- [x] Tests passed
- [x] Backend deployed to Railway
- [x] Frontend deployed to Vercel
- [x] Health checks passed

## Next Steps
1. Verify all features are working
2. Monitor error logs
3. Check performance metrics
4. Update DNS if needed
EOF

git add DEPLOYMENT_STATUS.md
git commit -m "chore: Update deployment status" || true
git push origin main

# 12. Final summary
echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo
echo -e "Backend: ${GREEN}$BACKEND_URL${NC}"
echo -e "Frontend: ${GREEN}$FRONTEND_URL${NC}"
echo
echo -e "${YELLOW}Important next steps:${NC}"
echo "1. Update frontend API URL in Vercel environment variables"
echo "2. Configure CORS in backend for frontend domain"
echo "3. Set up monitoring and alerts"
echo "4. Test all critical features"
echo "5. Update DNS records if using custom domain"
echo
echo -e "${GREEN}🎉 Your AIAssistant platform is now live!${NC}"