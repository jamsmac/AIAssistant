#!/bin/bash

echo "🧪 Running comprehensive test suite..."
echo "======================================"

# Set test environment
export TESTING=true
export ENVIRONMENT=test
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov pytest-mock httpx faker

# Run unit tests
echo ""
echo "🔬 Running unit tests..."
pytest tests/ -v --cov=api --cov-report=html --cov-report=term-missing --cov-report=json -m "unit or not slow"

# Check coverage threshold
COVERAGE=$(python3 << 'PYTHON'
import json
try:
    with open('coverage.json') as f:
        data = json.load(f)
        coverage = data['totals']['percent_covered']
        print(f"{coverage:.2f}")
except:
    print("0")
PYTHON
)

echo ""
echo "📊 Test Coverage: ${COVERAGE}%"

if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo "⚠️  WARNING: Coverage is below 80% threshold"
    exit 1
else
    echo "✅ Coverage meets 80% threshold"
fi

# Generate coverage badge
echo ""
echo "🎖️  Generating coverage badge..."
python3 << 'PYTHON'
import json

try:
    with open('coverage.json') as f:
        data = json.load(f)
        coverage = data['totals']['percent_covered']
        
    color = "red"
    if coverage >= 80:
        color = "green"
    elif coverage >= 60:
        color = "yellow"
    
    badge = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{coverage:.1f}%",
        "color": color
    }
    
    with open('coverage-badge.json', 'w') as f:
        json.dump(badge, f)
    
    print(f"✅ Coverage badge created: {coverage:.1f}% ({color})")
except Exception as e:
    print(f"❌ Failed to create badge: {e}")
PYTHON

echo ""
echo "📁 Coverage reports available:"
echo "   - HTML: htmlcov/index.html"
echo "   - JSON: coverage.json"
echo "   - Terminal: (shown above)"

echo ""
echo "✅ Test suite completed successfully!"
