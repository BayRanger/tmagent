#!/bin/bash
# Test runner script for TM-Agent

echo "========================================"
echo "🧪 Running TM-Agent Tests"
echo "========================================"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Run tests with pytest
python -m pytest tests/ -v --tb=short

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ ALL TESTS PASSED!"
    echo "========================================"
    exit 0
else
    echo ""
    echo "========================================"
    echo "❌ TESTS FAILED!"
    echo "========================================"
    exit 1
fi
