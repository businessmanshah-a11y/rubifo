#!/bin/bash

# Rubifo Local Development Runner

echo "🚀 Starting Rubifo Local Development Environment"
echo "================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check .env
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env from .env.example first"
    exit 1
fi

# Check database
echo -e "${BLUE}[1/5]${NC} Checking database..."
psql rubifo -c "SELECT 1" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Database 'rubifo' not found. Running setup..."
    createdb rubifo
    psql rubifo < migrations/001_init_schema.sql
    psql rubifo < migrations/002_post_and_schedule.sql
fi
echo -e "${GREEN}✅ Database ready${NC}"

# Check Python dependencies
echo -e "${BLUE}[2/5]${NC} Checking Python dependencies..."
python3 -c "import asyncpg" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip3 install -r requirements.txt --quiet
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"

# Create logs directory
echo -e "${BLUE}[3/5]${NC} Creating log files..."
mkdir -p logs
touch logs/bot.log logs/admin.log
echo -e "${GREEN}✅ Logs ready${NC}"

# Kill any existing instances first
pkill -f "python3 -m src.bot.main" 2>/dev/null || true
pkill -f "uvicorn src.admin.main" 2>/dev/null || true
sleep 1

# Start Bot
echo -e "${BLUE}[4/5]${NC} Starting Rubifo Bot..."
python3 -m src.bot.main > logs/bot.log 2>&1 &
BOT_PID=$!
echo -e "${GREEN}✅ Bot started (PID: $BOT_PID)${NC}"

# Start Admin Panel
echo -e "${BLUE}[5/5]${NC} Starting Admin Panel..."
python3 -m uvicorn src.admin.main:app --host 127.0.0.1 --port 8000 > logs/admin.log 2>&1 &
ADMIN_PID=$!
echo -e "${GREEN}✅ Admin Panel started (PID: $ADMIN_PID)${NC}"

echo ""
echo "================================================"
echo -e "${GREEN}✨ Rubifo is now running!${NC}"
echo "================================================"
echo ""
echo -e "${YELLOW}🌐 Admin Panel:${NC}"
echo "   URL: http://127.0.0.1:8000/admin/"
echo "   Username: admin"
echo "   Password: (see ADMIN_PASSWORD_HASH in .env)"
echo ""
echo -e "${YELLOW}🤖 Bot:${NC}"
echo "   Running in background"
echo "   Token: $(grep BOT_TOKEN .env | cut -d= -f2 | head -c 20)..."
echo ""
echo -e "${YELLOW}📊 Database:${NC}"
echo "   Server: localhost:5432"
echo "   Database: rubifo"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "   Bot: logs/bot.log"
echo "   Admin: logs/admin.log"
echo ""
echo -e "${YELLOW}🛑 To stop:${NC}"
echo "   kill $BOT_PID $ADMIN_PID"
echo "   Or: pkill -f 'python3 -m src.bot.main'"
echo ""
echo -e "${YELLOW}👀 Watch logs:${NC}"
echo "   tail -f logs/bot.log"
echo "   tail -f logs/admin.log"
echo ""

# Keep script running
wait
