#!/bin/bash

echo "🚀 Deploying Frontend to Vercel..."
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -d "web-ui" ]; then
    echo "❌ Error: web-ui directory not found!"
    exit 1
fi

# Navigate to web-ui directory
cd web-ui

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found!"
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo ""
echo "🔨 Building Next.js app..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "☁️  Deploying to Vercel..."
vercel --prod --yes

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ Deployment successful!"
    echo ""
    echo "Your app is now live on Vercel!"
    echo ""
    echo "To get the URL, run:"
    echo "  vercel inspect"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the logs above for details."
    exit 1
fi
