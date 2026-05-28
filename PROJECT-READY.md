# ✅ پروژه Rubifo آماده برای اجرا است!

**تاریخ**: ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵

---

## 🎯 خلاصه

پروژه **Rubifo** (ربات فوروارد هوشمند روبیکا) کاملاً برای اجرا آماده است.

### تمام موارد تکمیل‌شده:

✅ **Pre-Production** (P0-P7)  
✅ **Architecture & Tech Stack**  
✅ **Database Schema**  
✅ **75 Tasks** mapped with dependencies  
✅ **AI Instructions** (CLAUDE.md)  
✅ **IDE Setup** (.cursor/rules)  
✅ **Execution Tracking** (EXECUTION_TRACKER.md)  
✅ **Deployment Strategy** (Parspack)  

---

## 📋 فایل‌های اساسی

### Documentation
```
docs/
├── PRD.md                           ← نیازمندی‌های محصول
├── P2-feature-modules-breakdown.md  ← 10 ماژول
├── P3-technical-architecture.md     ← معماری Python+Rubpy
├── P5-user-journey-and-scope.md     ← User journeys
├── P7-WBS-and-milestones.md         ← 75 Tasks
├── EXECUTION_TRACKER.md             ← Status tracking
├── DEPLOYMENT-PARSPACK.md           ← Parspack guide
└── PRE-PRODUCTION-STATUS.md         ← Overview
```

### AI Instructions
```
CLAUDE.md                ← Claude/Codex AI guidelines
.cursor/rules            ← Cursor IDE rules
```

### Code Structure
```
src/
├── config.py            ← Configuration
├── database.py          ← DB utilities
├── bot/                 ← Bot logic
├── core/                ← Services
├── admin/               ← FastAPI dashboard
└── models/              ← Data models
```

---

## 🔧 اطلاعات فنی

### Stack
```
Language:       Python 3.10+
Bot:            Rubpy (async)
Database:       PostgreSQL
Admin:          FastAPI
DevOps:         Docker + systemd
Deployment:     Parspack (PaaS)
```

### Database Tables
```
users, subscriptions, transactions, routes, post_queue,
schedules, schedule_times, logs
```

### 75 Tasks
```
M0: Setup (5)        → T01-T05
M1: User Mgmt (7)    → T06-T12
M2: Payment (7)      → T13-T19
M3: Routes (9)       → T20-T28
M4: Scheduling (12)  → T29-T40
M5: Commands (10)    → T41-T50
M6: Admin (12)       → T51-T62
M7: QA (8)           → T63-T70
M8: Deploy (5)       → T71-T75
```

---

## 🚀 شروع کردن

### برای Developers

**Step 1: Setup Local Environment**
```bash
git clone https://github.com/businessmanshah-a11y/rubifo.git
cd rubifo

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your values

docker-compose up -d postgres
python -m src.database
```

**Step 2: Select Task**
```
1. Open docs/P7-WBS-and-milestones.md
2. Find first available task (check EXECUTION_TRACKER.md)
3. Start with T01 (Setup & Database milestone)
```

**Step 3: Follow CLAUDE.md**
```
Read: CLAUDE.md
- How to start task
- Code guidelines
- When to commit
- Risk/issue logging
```

**Step 4: Use Cursor IDE**
```
1. Install Parspack extension (optional)
2. Follow .cursor/rules
3. Code following guidelines
4. Run: python -m src.bot.main
```

**Step 5: Commit & Track**
```
git commit -m "T##: task description"
Update: docs/EXECUTION_TRACKER.md
```

### برای DevOps/مدیریت

**Deployment Setup**
```
1. Read: docs/DEPLOYMENT-PARSPACK.md
2. Create Parspack account
3. Install VSCode Parspack extension
4. Create project in Parspack
5. Set environment variables
6. Deploy on M8 milestone
```

---

## 📊 Execution Tracker

**جدول وضعیت تمام 75 task:**

```
docs/EXECUTION_TRACKER.md

Format:
- Task ID: T01-T75
- Status: ⏳ Pending / 🔄 In Progress / ✅ Done
- Issues: Log any problems
- Risks: Log any risks
```

**چگونه آپدیت کنیم:**

```markdown
# قبل از شروع
| T01 | ... | ⏳ Pending | - | - |

# هنگام انجام
| T01 | ... | 🔄 In Progress | 2026-05-15 | - |

# بعد از اتمام
| T01 | ... | ✅ Done | 2026-05-15 | 2026-05-15 |
```

---

## 🤖 AI Agent Instructions

### برای Claude

**فایل**: `CLAUDE.md`

**شامل:**
- ✅ Project overview
- ✅ Code guidelines (PEP 8, async, type hints)
- ✅ Architecture rules
- ✅ Commit standards
- ✅ Risk/issue logging
- ✅ Testing expectations
- ✅ When to ask for help

**چگونه استفاده کنیم:**
```
1. Read CLAUDE.md completely
2. Select task from P7-WBS
3. Update EXECUTION_TRACKER to "In Progress"
4. Code following guidelines
5. When done: commit + push
6. Update tracker to "Done"
```

### برای Cursor IDE

**فایل**: `.cursor/rules`

**شامل:**
- ✅ Cursor-specific patterns
- ✅ Do's and Don'ts
- ✅ Folder structure
- ✅ Git workflow
- ✅ Code quality checklist
- ✅ Common patterns
- ✅ Quick reference

**چگونه فعال شود:**
```
Cursor automatically loads .cursor/rules
اگر نه، دستی load کنید:
Cmd+Shift+P → "Cursor: Load Rules"
```

---

## 📈 Progress Tracking

### Visual Progress

```
Total Tasks: 75
Status: 0 Done, 0 In Progress, 75 Pending

Progress: ▭▭▭▭▭▭▭▭▭▭ 0%
```

### Tracking Tools

```
1. EXECUTION_TRACKER.md      ← Main tracker
2. GitHub Issues              ← For bugs/blockers
3. Commit history             ← Via git log
4. CLAUDE.md                  ← For guidelines
```

---

## ⚠️ Risk Management

### معروف Risks

```
Risk #1: Single Bot Instance
- Impact: High
- Mitigation: Auto-restart via systemd
- Post-V1: Distributed execution

Risk #2: Payment Polling (5min timeout)
- Impact: Medium
- Mitigation: Good error messages
- Post-V1: Webhook integration

Risk #3: Rate Limiting (0.5s/call)
- Impact: Low
- Mitigation: Async design handles it
```

### Issue Logging

```
جب bug یا issue ملے:

### Issue #X
- Task: T##
- Description: کیا غلط ہے
- Status: Open
- Resolution: کیسے ٹھیک کریں
```

---

## 🛠️ Development Workflow

### روزانہ Workflow

```
1. Morning:
   - Check EXECUTION_TRACKER
   - Select next available task
   - Read task in P7-WBS

2. Development:
   - Open CLAUDE.md
   - Follow code guidelines
   - Write tests
   - Commit frequently

3. Evening:
   - Final commit with task complete
   - Push to GitHub
   - Update EXECUTION_TRACKER
   - Log any issues/risks

4. Summary:
   - git log T##
   - docs updated?
   - Tests passing?
   - Ready for next task?
```

### Weekly Standup

```
Checklist:
- [ ] How many tasks completed?
- [ ] Any blockers?
- [ ] Any risks identified?
- [ ] Tests passing?
- [ ] Documentation updated?
- [ ] Next milestone on track?
```

---

## 🌐 Deployment (Parspack)

### Requirements

```
1. Parspack account
2. VSCode with Parspack extension
3. PostgreSQL database (Parspack managed)
4. .env with all variables
```

### 3-Step Deploy

```
1. VSCode → Cmd+Shift+P → "Parspack: Create Project"
2. Configure project (rubifo-bot)
3. Cmd+Shift+P → "Parspack: Deploy"
```

### Post-Deploy

```
✅ Check health: /admin/health
✅ View logs: "Parspack: View Logs"
✅ Test bot: /start command
✅ Monitor: Dashboard
```

---

## 📝 Quality Standards

### Code Quality

```
✅ PEP 8 compliance
✅ Type hints everywhere
✅ Docstrings for all functions
✅ Error handling complete
✅ Tests with every feature
✅ No hardcoded values
✅ No global state
✅ Async/await used correctly
```

### Testing

```
✅ Unit tests (80%+ coverage)
✅ Integration tests
✅ E2E tests
✅ Manual testing
✅ Performance testing (M7)
```

### Documentation

```
✅ Code comments (when needed)
✅ Docstrings (all functions)
✅ README updated
✅ API docs (FastAPI auto)
✅ EXECUTION_TRACKER updated
```

---

## 🎯 Success Metrics

### V1 Launch Criteria

```
✅ All 75 tasks complete
✅ All tests passing
✅ 80%+ code coverage
✅ Zero critical bugs
✅ Performance target met (60s max latency)
✅ Documentation complete
✅ Deployment automated
✅ Team trained
✅ Monitoring in place
✅ Backup strategy tested
```

---

## 📚 Quick Reference

### Key Docs
```
PRD                          → What we're building
P7-WBS                       → How to break it down
CLAUDE.md                    → How to code it
.cursor/rules                → IDE guidelines
DEPLOYMENT-PARSPACK.md       → How to deploy
EXECUTION_TRACKER.md         → Track progress
```

### Key Commands
```
git checkout -b T##-name                    # Start task
python -m src.bot.main                      # Run bot
python -m src.admin.main                    # Run admin
pytest tests/                               # Run tests
git commit -m "T##: description"            # Commit
git push origin T##-name                    # Push
```

### Key Folders
```
src/                         → Source code
docs/                        → Documentation
tests/                       → Test suite
migrations/                  → DB migrations
.cursor/                     → IDE config
```

---

## ❓ سوالات متداول

**Q: کہاں سے شروع کروں?**  
A: T01 سے (Setup milestone). CLAUDE.md پڑھیں.

**Q: کیا ORM استعمال کروں?**  
A: نہیں! asyncpg صرف. CLAUDE.md دیکھیں.

**Q: اگر task dependencies ختم نہیں?**  
A: دوسری task منتخب کریں. EXECUTION_TRACKER دیکھیں.

**Q: اگر bug ملے?**  
A: EXECUTION_TRACKER میں log کریں. گھبرائیں نہیں!

**Q: کیا scope سے باہر جا سکتا ہوں?**  
A: نہیں! صرف assigned task. CLAUDE.md کہتا ہے.

**Q: کیا ہر commit push کروں?**  
A: ہاں. Final commit task complete ہو تو push.

**Q: Parspack کب?**  
A: M8 میلستون (آخری). DEPLOYMENT-PARSPACK.md پڑھیں.

---

## 🎉 Next Steps

```
┌─────────────────────────────────────────┐
│  1. CLAUDE.md پوری پڑھیں                 │
│  2. T01 منتخب کریں (Setup milestone)     │
│  3. گیٹ برانچ بنائیں (T01-init-project)  │
│  4. کوڈ لکھیں (guidelines کے ساتھ)      │
│  5. Commit + Push کریں                   │
│  6. EXECUTION_TRACKER آپ ڈیٹ کریں         │
│  7. اگلی task                          │
│  8. Repeat 75 بار! 🚀                    │
└─────────────────────────────────────────┘
```

---

## ✨ خلاصہ

**Rubifo** اب مکمل طور پر documented اور orchestrated ہے:

- ✅ **Product**: واضح طور پر defined
- ✅ **Architecture**: proven stack
- ✅ **Tasks**: 75 clearly mapped tasks
- ✅ **Process**: AI-first workflow
- ✅ **Tracking**: Real-time progress
- ✅ **Deployment**: Automated via Parspack
- ✅ **Guidelines**: Clear for everyone

**آپ اب شروع کر سکتے ہیں! 🎯**

---

## 📞 Support Resources

```
Documentation:  docs/
AI Guidelines:  CLAUDE.md
IDE Rules:      .cursor/rules
Task Tracking:  docs/EXECUTION_TRACKER.md
Deployment:     docs/DEPLOYMENT-PARSPACK.md
Architecture:   docs/P3-technical-architecture.md
Tasks:          docs/P7-WBS-and-milestones.md
```

---

**تاریخ تیاری**: ۱۴۰۵/۰۲/۲۵ (2026-05-15)  
**وضعیت**: ✅ READY FOR EXECUTION  
**اگلی مرحلہ**: T01 شروع کریں

