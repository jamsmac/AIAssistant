#!/bin/bash
# Production CORS Configuration Setup
# Sets CORS_ORIGINS and other production environment variables in Railway

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  PRODUCTION CORS CONFIGURATION SETUP"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Or use Railway Dashboard:"
    echo "  https://railway.app/dashboard"
    exit 1
fi

# Check if logged in
echo "Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "⚠️  Not logged in to Railway"
    echo ""
    echo "Please login:"
    read -p "Press Enter to login to Railway..."
    railway login
fi

echo "✓ Railway CLI authenticated"
echo ""

# Get current project
echo "Current Railway project:"
railway status || echo "⚠️  No project linked"
echo ""

# Ask for frontend URL
echo "Enter your production frontend URL(s):"
echo "Example: https://your-app.vercel.app"
echo "Multiple URLs: https://app.com,https://www.app.com"
echo ""
read -p "Frontend URL(s): " FRONTEND_URLS

if [ -z "$FRONTEND_URLS" ]; then
    echo "❌ Frontend URL is required!"
    exit 1
fi

# Confirm
echo ""
echo "Configuration to set:"
echo "  CORS_ORIGINS = $FRONTEND_URLS"
echo ""
read -p "Proceed? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

# Set variables
echo ""
echo "Setting Railway variables..."

railway variables set CORS_ORIGINS="$FRONTEND_URLS"
railway variables set FRONTEND_URL="$(echo $FRONTEND_URLS | cut -d',' -f1)"

# Also set ENVIRONMENT to production if not set
if ! railway variables get ENVIRONMENT &> /dev/null; then
    railway variables set ENVIRONMENT="production"
    echo "✓ Set ENVIRONMENT=production"
fi

echo ""
echo "✓ CORS configuration updated!"
echo ""

# Show current configuration
echo "Current CORS configuration:"
railway variables | grep -E "CORS_ORIGINS|FRONTEND_URL|ENVIRONMENT"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  NEXT STEPS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Redeploy your Railway service:"
echo "   railway up --detach"
echo ""
echo "2. Or trigger redeploy in Dashboard:"
echo "   https://railway.app/dashboard → Your Project → Redeploy"
echo ""
echo "3. Test CORS after deployment:"
echo "   curl -I https://your-railway-app.railway.app/api/health \\"
echo "     -H \"Origin: https://your-frontend.vercel.app\""
echo ""
echo "   Should return:"
echo "   Access-Control-Allow-Origin: https://your-frontend.vercel.app"
echo ""
echo "═══════════════════════════════════════════════════════════"
