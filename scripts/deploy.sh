#!/bin/bash

# Production Deployment Script
# Usage: ./scripts/deploy.sh [environment] [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
BRANCH=${2:-main}
DEPLOY_DIR="/Users/js/autopilot-core"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi

    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        exit 1
    fi

    log_info "All requirements met ✓"
}

# Pre-deployment checks
pre_deploy_checks() {
    log_info "Running pre-deployment checks..."

    # Check git status
    if [[ $(git status --porcelain) ]]; then
        log_warn "There are uncommitted changes"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        log_info "Switching to branch: $BRANCH"
        git checkout $BRANCH
        git pull origin $BRANCH
    fi

    log_info "Pre-deployment checks passed ✓"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."

    cd $DEPLOY_DIR/web-ui
    npm ci --production=false

    cd $DEPLOY_DIR
    pip install -r requirements.txt

    log_info "Dependencies installed ✓"
}

# Run tests
run_tests() {
    log_info "Running tests..."

    cd $DEPLOY_DIR/web-ui

    # Type checking
    log_info "Running type check..."
    npm run type-check

    # Linting
    log_info "Running linter..."
    npm run lint

    # Unit tests
    log_info "Running unit tests..."
    npm test

    # Security audit
    log_info "Running security audit..."
    npm audit --production

    log_info "All tests passed ✓"
}

# Build application
build_application() {
    log_info "Building application for $ENVIRONMENT..."

    cd $DEPLOY_DIR/web-ui

    # Set environment
    export NODE_ENV=$ENVIRONMENT

    # Load environment variables
    if [ -f ".env.$ENVIRONMENT" ]; then
        export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
    fi

    # Build Next.js app
    npm run build

    # Check build size
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Analyzing bundle size..."
        npx next-bundle-analyzer
    fi

    log_info "Build completed ✓"
}

# Database migrations
run_migrations() {
    log_info "Running database migrations..."

    cd $DEPLOY_DIR

    # Run Supabase migrations
    if command -v supabase &> /dev/null; then
        supabase db push --include-all
    else
        log_warn "Supabase CLI not found, skipping migrations"
    fi

    log_info "Migrations completed ✓"
}

# Deploy to platform
deploy_to_platform() {
    log_info "Deploying to $ENVIRONMENT..."

    case $ENVIRONMENT in
        production)
            deploy_to_vercel_production
            ;;
        staging)
            deploy_to_vercel_staging
            ;;
        development)
            log_info "Development deployment - running locally"
            cd $DEPLOY_DIR/web-ui
            npm run dev
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Deploy to Vercel (Production)
deploy_to_vercel_production() {
    log_info "Deploying to Vercel Production..."

    cd $DEPLOY_DIR/web-ui

    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        log_info "Installing Vercel CLI..."
        npm i -g vercel
    fi

    # Deploy with production flag
    vercel --prod --yes

    log_info "Vercel production deployment completed ✓"
}

# Deploy to Vercel (Staging)
deploy_to_vercel_staging() {
    log_info "Deploying to Vercel Staging..."

    cd $DEPLOY_DIR/web-ui

    # Deploy without production flag (creates preview URL)
    vercel --yes

    log_info "Vercel staging deployment completed ✓"
}

# Post-deployment tasks
post_deploy_tasks() {
    log_info "Running post-deployment tasks..."

    # Warm up endpoints
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Warming up production endpoints..."

        PROD_URL=${NEXT_PUBLIC_PRODUCTION_URL:-"https://your-app.vercel.app"}

        curl -s -o /dev/null -w "%{http_code}" $PROD_URL
        curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/health
    fi

    # Clear CDN cache
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Clearing CDN cache..."
        # Add your CDN cache clearing command here
    fi

    # Send notification
    send_deployment_notification

    log_info "Post-deployment tasks completed ✓"
}

# Send deployment notification
send_deployment_notification() {
    log_info "Sending deployment notification..."

    COMMIT_HASH=$(git rev-parse --short HEAD)
    COMMIT_MESSAGE=$(git log -1 --pretty=%B)
    DEPLOYER=$(git config user.name)

    MESSAGE="🚀 Deployment to $ENVIRONMENT completed!

Branch: $BRANCH
Commit: $COMMIT_HASH
Message: $COMMIT_MESSAGE
Deployed by: $DEPLOYER
Time: $(date '+%Y-%m-%d %H:%M:%S')"

    # Send to Slack (if webhook is configured)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$MESSAGE\"}" \
            $SLACK_WEBHOOK_URL
    fi

    echo -e "${GREEN}$MESSAGE${NC}"
}

# Rollback function
rollback() {
    log_error "Deployment failed! Starting rollback..."

    # Revert to previous deployment in Vercel
    if [ "$ENVIRONMENT" = "production" ]; then
        vercel rollback --yes
    fi

    log_info "Rollback completed"
    exit 1
}

# Set up error handling
trap rollback ERR

# Main deployment flow
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Deployment Script v1.0${NC}"
    echo -e "${GREEN}    Environment: $ENVIRONMENT${NC}"
    echo -e "${GREEN}    Branch: $BRANCH${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo

    check_requirements
    pre_deploy_checks
    install_dependencies
    run_tests
    build_application
    run_migrations
    deploy_to_platform
    post_deploy_tasks

    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}    Deployment Successful! 🎉${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main