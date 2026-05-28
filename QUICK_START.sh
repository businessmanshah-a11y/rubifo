#!/bin/bash

# Rubifo Quick Start Guide

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        🚀 RUBIFO QUICK START - LOCAL TESTING MODE 🚀        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}📋 STEP 1: Generate Admin Password${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Run this to generate bcrypt hash:"
echo ""
echo "  python3 << 'PY'"
echo "  import bcrypt"
echo "  password = 'admin123'  # Change this!"
echo "  hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()"
echo "  print(f'ADMIN_PASSWORD_HASH={hash}')"
echo "  PY"
echo ""
echo -e "${YELLOW}Copy the hash and update .env${NC}"
echo ""

echo -e "${YELLOW}📋 STEP 2: Update .env File${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  nano .env"
echo "  # Paste the ADMIN_PASSWORD_HASH"
echo ""

echo -e "${YELLOW}📋 STEP 3: Start Services${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Option A - Automatic (Recommended):${NC}"
echo "  bash run_local.sh"
echo ""
echo -e "${GREEN}Option B - Manual (2 Terminals):${NC}"
echo ""
echo "  Terminal 1 (Bot):"
echo "    python3 -m src.bot.main"
echo ""
echo "  Terminal 2 (Admin Panel):"
echo "    uvicorn src.admin.main:app --host 127.0.0.1 --port 8000 --reload"
echo ""

echo -e "${YELLOW}📋 STEP 4: Access Admin Panel${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  URL: http://127.0.0.1:8000/admin/"
echo "  Username: admin"
echo "  Password: (what you set above)"
echo ""

echo -e "${YELLOW}📋 STEP 5: Test Dashboard${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Check these pages:"
echo "  • Dashboard: http://127.0.0.1:8000/admin/dashboard.html"
echo "  • Users: http://127.0.0.1:8000/admin/users.html"
echo "  • Logs: http://127.0.0.1:8000/admin/logs.html"
echo ""

echo -e "${YELLOW}📋 STEP 6: Run Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  pytest tests/ -v"
echo ""

echo -e "${YELLOW}📋 TEST DATA:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  User ID:     987654321"
echo "  Username:    testuser"
echo "  Tier:        basic (1 route limit)"
echo "  Trial:       48 hours"
echo "  Routes:      1 active (12345 → 67890)"
echo "  Schedules:   1 (5-min interval)"
echo ""

echo -e "${GREEN}✨ Ready to go! Follow the steps above.${NC}"
echo ""
