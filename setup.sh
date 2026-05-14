#!/bin/bash
# AIQE CrewAI - Setup Script
# Run: bash setup.sh

set -e

echo "======================================"
echo "  AIQE CrewAI - Setup Starting..."
echo "======================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "  ✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your real credentials:"
echo "   - API_KEY=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"
echo "   - JIRA_USER=HoaDTT25@fpt.com"
echo "   - JIRA_TOKEN=ATATT3xFfGF0qsC_31Nc0JNicNulyrRzgjQZAXy1xWWn44Oq20KeJ6LHUH-cY19cOjoirIJvCRR2aCU3Fmzu-bn75-Vp_6A2tOmOW0HhHDisWTmoZ59_PsznsnDHjSPaVYkRSqgeckH6nWK9ad1XLsH2auhpjiMI5rHgI6F7xaz71aTFKbEmuRA=0608FBAC"
echo ""
echo "2. Add your skill prompts in prompts/ folder:"
echo "   - prompts/business_analysis.md"
echo "   - prompts/manual_testcase.md"
echo "   - prompts/automation_testcase.md"
echo "   - prompts/java_testng_maven_example.md"
echo ""
echo "3. Run the Web UI:"
echo "   source venv/bin/activate"
echo "   streamlit run app.py"
echo ""
echo "   Or CLI mode:"
echo "   python main.py"
echo ""