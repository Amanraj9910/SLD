#!/bin/bash
# SLD Processing Platform - Linux/Mac Installation Script

set -e  # Exit on any error

echo "🚀 SLD Processing Platform - Installation Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check if Python is installed
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        echo "Please install Python 3.8+ from https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
print_status "Python $PYTHON_VERSION is available"

# Check if pip is installed
print_info "Checking pip installation..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    print_error "pip is not installed"
    echo "Please install pip first"
    exit 1
fi
print_status "pip is available"

# Check if Node.js is installed
print_info "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    echo "Please install Node.js 16+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version)
print_status "Node.js $NODE_VERSION is available"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    echo "Please install npm (usually comes with Node.js)"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_status "npm $NPM_VERSION is available"

# Run Python installation script
echo ""
print_info "Running Python dependency installation..."
$PYTHON_CMD install.py

if [ $? -ne 0 ]; then
    print_error "Python installation failed"
    exit 1
fi

# Install frontend dependencies
echo ""
print_info "Installing frontend dependencies..."

if [ ! -d "web_app/frontend" ]; then
    print_error "Frontend directory not found: web_app/frontend"
    exit 1
fi

cd web_app/frontend

if [ ! -f "package.json" ]; then
    print_error "package.json not found in web_app/frontend"
    exit 1
fi

print_info "Installing Node.js packages..."
npm install

if [ $? -ne 0 ]; then
    print_error "Frontend installation failed"
    exit 1
fi

cd ../..

echo ""
echo "================================================"
print_status "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the backend:"
echo "   cd web_app/backend"
echo "   python main.py"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd web_app/frontend"
echo "   npm start"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Check README.md for more detailed instructions"
echo "================================================"
