# P7 - WBS و برنامه فازبندی
**تاریخ:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت:** ✅ تمام

---

## نمای کلی Milestones

| Milestone | عنوان | Duration | Tasks |
|-----------|-------|----------|-------|
| **M0** | Setup & Database | ۲ روز | T01-T05 |
| **M1** | User & Auth System | ۳ روز | T06-T12 |
| **M2** | Subscription & Payment | ۳ روز | T13-T19 |
| **M3** | Route & Queue System | ۳ روز | T20-T28 |
| **M4** | Schedule & Execution | ۴ روز | T29-T40 |
| **M5** | Bot Commands & UX | ۳ روز | T41-T50 |
| **M6** | Admin Dashboard | ۴ روز | T51-T62 |
| **M7** | Testing & QA | ۳ روز | T63-T70 |
| **M8** | Deployment & Launch | ۲ روز | T71-T75 |

**Total: ~25-27 days for full V1 development**

---

## M0 - Setup & Database Infrastructure

### T01: Initialize project structure and dependencies
- **Owner**: Backend Lead
- **Duration**: 4 hours
- **Description**:
  - Create folder structure (src/, tests/, docs/, migrations/)
  - Setup requirements.txt with all deps
  - Setup .env.example
  - Create Docker files (Dockerfile, docker-compose.yml)
  - Setup logging config (logger.py)
- **Output**: Runnable project skeleton
- **Dependencies**: None
- **Status**: ⏳ Pending → Ready for T02

### T02: Setup PostgreSQL & asyncpg connection pool
- **Owner**: Backend Lead
- **Duration**: 2 hours
- **Description**:
  - Create src/database.py with init_db() and connection pool
  - Test connection with docker-compose postgres
  - Setup .env for DATABASE_URL
- **Output**: Functional DB connection pool
- **Dependencies**: T01
- **Status**: ⏳ Pending

### T03: Create database schema (users, subscriptions, transactions)
- **Owner**: Database/Backend
- **Duration**: 3 hours
- **Description**:
  - Write migrations/001_init_schema.sql
  - Create users table with trial fields
  - Create subscriptions and transactions tables
  - Create indexes for performance
- **Output**: migrations/001_init_schema.sql
- **Dependencies**: T02
- **Status**: ⏳ Pending

### T04: Create database schema (routes, queues, schedules)
- **Owner**: Database/Backend
- **Duration**: 3 hours
- **Description**:
  - Create routes, post_queue, schedules tables
  - Create schedule_times table
  - Create logs table
  - Test schema with sample data
- **Output**: migrations/002_post_and_schedule.sql
- **Dependencies**: T03
- **Status**: ⏳ Pending

### T05: Setup Rubpy client and async bot skeleton
- **Owner**: Backend Lead
- **Duration**: 3 hours
- **Description**:
  - Create src/bot/client.py wrapper around Rubpy
  - Setup basic message handler
  - Test connection to Rubika (sandbox or test account)
  - Document Rubpy API usage
- **Output**: Working Rubpy client and main loop
- **Dependencies**: T01
- **Status**: ⏳ Pending

---

## M1 - User & Auth System

### T06: Create User model and database access layer
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create src/models/user.py
  - Create src/core/user_service.py with CRUD operations
  - Implement get_or_create_user()
- **Output**: user_service.py with full CRUD
- **Dependencies**: T03
- **Status**: ⏳ Pending

### T07: Implement /start command (user registration & trial)
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - Implement /start handler in src/bot/commands.py
  - Call user_service.get_or_create_user()
  - Set trial_start and trial_end (48 hours)
  - Send welcome message with commands list
  - Test with test account
- **Output**: /start command working
- **Dependencies**: T06, T05
- **Status**: ⏳ Pending

### T08: Implement trial reminder loop (24h before end)
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create trial_reminder_loop() in src/bot/main.py
  - Run every 60 minutes
  - Check users with trial_end <= NOW() + 1 day
  - Send reminder message "Trial ending in 24h, /buy to continue"
- **Output**: Async reminder loop
- **Dependencies**: T07
- **Status**: ⏳ Pending

### T09: Implement trial expiration logic
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Check on every user action if trial expired
  - If expired and no subscription, disable all routes/plans
  - Send "Trial expired" message
- **Output**: Trial expiration handler
- **Dependencies**: T08
- **Status**: ⏳ Pending

### T10: Create Subscription model and service
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create src/models/subscription.py
  - Create src/core/subscription_service.py
  - Implement get_active_subscription(), check_route_limit()
- **Output**: subscription_service.py
- **Dependencies**: T06
- **Status**: ⏳ Pending

### T11: Implement /buy command (subscription tiers)
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Display 3 tiers: Basic, Pro, Enterprise
  - Allow user to select tier
  - Show invoice and total amount
  - Move to payment flow (next milestone)
- **Output**: /buy command structure
- **Dependencies**: T10
- **Status**: ⏳ Pending

### T12: Add admin authentication (JWT + session)
- **Owner**: Backend/Admin
- **Duration**: 2 hours
- **Description**:
  - Create src/admin/auth.py
  - Implement username/password hashing with bcrypt
  - Create JWT token generation
  - Add auth middleware for FastAPI
- **Output**: JWT + session cookie auth system
- **Dependencies**: T01
- **Status**: ⏳ Pending

---

## M2 - Subscription & Payment

### T13: Integrate Zarinpal payment gateway
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - Create src/integrations/zarinpal.py
  - Implement request_payment() method
  - Implement verify_payment() method
  - Handle errors and edge cases
  - Test with sandbox account
- **Output**: zarinpal.py with request/verify
- **Dependencies**: T11
- **Status**: ⏳ Pending

### T14: Implement payment verification flow (polling)
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - After payment link sent, start polling
  - Check every 10 seconds for 5 minutes
  - On success: create subscription record، activate routes، send confirmation
  - On timeout: send "Payment not verified" and ask to try again
- **Output**: Polling verification loop
- **Dependencies**: T13
- **Status**: ⏳ Pending

### T15: Implement transaction history storage
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Insert transaction record in DB (amount, status, reference_id)
  - Store for future reference and analytics
  - Create transaction_service.py
- **Output**: transaction_service.py
- **Dependencies**: T14
- **Status**: ⏳ Pending

### T16: Implement subscription tier enforcement (route limits)
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - When creating route, check if user has reached limit
  - If at limit, send "You've reached X routes limit. Upgrade your plan."
  - If user upgrades، check if needs to delete routes
  - Disable routes if too many for new tier
- **Output**: Route limit checking in route_service
- **Dependencies**: T10
- **Status**: ⏳ Pending

### T17: Create /buy command payment flow
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - After user selects tier، show invoice
  - Generate payment link via Zarinpal
  - Send payment link to user
  - Start polling for verification
- **Output**: Complete /buy flow
- **Dependencies**: T13, T14
- **Status**: ⏳ Pending

### T18: Implement manual subscription renewal (/renew command)
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create /renew command
  - Show current subscription end date
  - Allow user to renew for 30 more days
  - Generate new payment link
  - Test renewal flow
- **Output**: /renew command and renewal logic
- **Dependencies**: T17
- **Status**: ⏳ Pending

### T19: Create admin payment dashboard (view transactions)
- **Owner**: Admin
- **Duration**: 2 hours
- **Description**:
  - Add API endpoint /admin/transactions
  - Display all transactions with filters (date, user, status)
  - Show revenue stats
  - Allow export to CSV
- **Output**: Admin transactions view
- **Dependencies**: T12, T15
- **Status**: ⏳ Pending

---

## M3 - Route & Queue System

### T20: Create Route and PostQueue models
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create src/models/route.py
  - Create src/models/post_queue.py
  - Create src/core/route_service.py and queue_service.py
- **Output**: Models and service layer for routes/queues
- **Dependencies**: T03, T04
- **Status**: ⏳ Pending

### T21: Implement /addroute command (part 1 - channel validation)
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - Implement /addroute handler
  - Ask for source channel ID/username
  - Ask for target channel ID/username
  - Validate bot is admin in both channels using Rubpy
  - Send error if not admin، ask to try again
- **Output**: /addroute command up to permission check
- **Dependencies**: T20, T05
- **Status**: ⏳ Pending

### T22: Implement /addroute command (part 2 - initial queue population)
- **Owner**: Backend
- **Duration**: 4 hours
- **Description**:
  - Read all existing posts from source channel
  - Handle Rubika API pagination (100 posts at a time)
  - Apply 0.5s rate limit between requests
  - Insert all posts into post_queue with status='pending'
  - Order by source_date ascending
  - Send confirmation with route_id and queue size
- **Output**: /addroute complete
- **Dependencies**: T21
- **Status**: ⏳ Pending

### T23: Implement /listroutes command
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Show all user's routes with source → target
  - Show is_active status
  - Show number of plans per route
  - Show queue size
- **Output**: /listroutes command
- **Dependencies**: T22
- **Status**: ⏳ Pending

### T24: Implement /removeroute command
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Ask for confirmation before deleting
  - Delete route، all plans، and queue entries
  - Send confirmation
- **Output**: /removeroute command
- **Dependencies**: T23
- **Status**: ⏳ Pending

### T25: Implement /updatesource command (add new posts)
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - Fetch latest posts from source since last sync
  - Filter out posts already in queue (by message_id)
  - Add new posts to END of queue (preserve order)
  - Show count of new posts added
  - Test with actual new posts in channel
- **Output**: /updatesource command
- **Dependencies**: T22
- **Status**: ⏳ Pending

### T26: Implement /sync command (remove deleted posts)
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - For each pending post in queue، check if still exists in source
  - If deleted، mark as 'removed' and log
  - This can be async and show "syncing..." message
  - Show count of removed posts
- **Output**: /sync command
- **Dependencies**: T22
- **Status**: ⏳ Pending

### T27: Add post queue management logic
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Implement get_next_post() method (FIFO، status='pending')
  - Implement mark_as_sent() and mark_as_failed()
  - Implement retry_count increment
  - Test with multiple posts
- **Output**: Post queue manipulation methods
- **Dependencies**: T20
- **Status**: ⏳ Pending

### T28: Create admin route management view
- **Owner**: Admin
- **Duration**: 2 hours
- **Description**:
  - Add /admin/routes API endpoint
  - Show all routes with user، queue size، status
  - Allow filter and search
- **Output**: Admin routes view
- **Dependencies**: T12
- **Status**: ⏳ Pending

---

## M4 - Schedule & Execution Engine

### T29: Create Schedule model and service
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create src/models/schedule.py
  - Create src/core/schedule_service.py
  - Implement CRUD operations
- **Output**: Schedule model and service
- **Dependencies**: T04
- **Status**: ⏳ Pending

### T30: Implement /addplan command (part 1 - interval method)
- **Owner**: Backend
- **Duration**: 4 hours
- **Description**:
  - Ask schedule type (interval or daily_count)
  - For interval: ask start_time، end_time، interval_minutes، days_of_week
  - Ask posts_per_run
  - Ask loop_mode (one-shot or infinite)
  - Calculate first next_run
  - Create schedule record
- **Output**: Interval method plan creation
- **Dependencies**: T29
- **Status**: ⏳ Pending

### T31: Implement /addplan command (part 2 - daily count method)
- **Owner**: Backend
- **Duration**: 4 hours
- **Description**:
  - For daily_count: ask posts_per_day، start_hour، end_hour، days_of_week
  - Calculate distribution of posts across hours
  - Ask user to confirm or edit times
  - Store schedule_times records
  - Calculate first next_run
- **Output**: Daily count method plan creation
- **Dependencies**: T30
- **Status**: ⏳ Pending

### T32: Implement next_run calculation logic
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - For interval: next_run = now + interval_minutes
  - If crosses end_time، jump to next_day start_time
  - For daily_count: fetch next time from schedule_times
  - Handle day_of_week constraints
  - Test with various scenarios
- **Output**: next_run calculation functions
- **Dependencies**: T30, T31
- **Status**: ⏳ Pending

### T33: Implement /listplans command
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Show all plans for a route
  - Display schedule info، next_run، is_active، loop_mode
- **Output**: /listplans command
- **Dependencies**: T30
- **Status**: ⏳ Pending

### T34: Implement /editplan command
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - Allow editing schedule parameters (not loop_mode in V1)
  - Update next_run after changes
  - Test that changes take effect immediately
- **Output**: /editplan command
- **Dependencies**: T33
- **Status**: ⏳ Pending

### T35: Implement /removeplan command
- **Owner**: Backend
- **Duration**: 1 hour
- **Description**:
  - Ask for confirmation
  - Delete plan and related schedule_times
  - Send confirmation
- **Output**: /removeplan command
- **Dependencies**: T33
- **Status**: ⏳ Pending

### T36: Implement /toggleplan command
- **Owner**: Backend
- **Duration**: 1 hour
- **Description**:
  - Toggle is_active for a plan
  - Send status confirmation
- **Output**: /toggleplan command
- **Dependencies**: T33
- **Status**: ⏳ Pending

### T37: Create execution_engine.py (main loop)
- **Owner**: Backend
- **Duration**: 4 hours
- **Description**:
  - Create src/core/execution_engine.py
  - Implement main loop running every 30 seconds
  - Fetch active schedules with next_run <= NOW()
  - For each schedule، execute in transaction:
    - SELECT FOR UPDATE on post_queue
    - Get next pending post
    - Forward message
    - Handle errors/retry
    - Update next_run
  - Test with mock posts and schedules
- **Output**: execution_engine.py with full execution logic
- **Dependencies**: T29, T27
- **Status**: ⏳ Pending

### T38: Implement message forwarding to target channel
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Create forward_message() function in src/core/execution_engine.py
  - Handle rate limiting (0.5s between requests)
  - Try to forward message
  - Catch errors (channel not found، bot not admin، deleted post، etc.)
  - Return success/error
- **Output**: forward_message() function
- **Dependencies**: T37
- **Status**: ⏳ Pending

### T39: Implement error handling and retry logic
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - If forward fails، increment retry_count and last_error
  - If < 3: set next_run to NOW() + 5 minutes، continue
  - If == 3: mark post as 'failed'، log error، continue
  - If critical error (not admin، channel missing): deactivate schedule، message user
  - Test all retry scenarios
- **Output**: Retry logic integrated in engine
- **Dependencies**: T38
- **Status**: ⏳ Pending

### T40: Implement queue reset for loop_mode
- **Owner**: Backend
- **Duration**: 3 hours
- **Description**:
  - When queue becomes empty:
    - If loop_mode=true: re-read all posts from source، reset to pending
    - If loop_mode=false: deactivate schedule، send message
  - Handle last_loop_reset_at to avoid re-sending old posts
  - Test both scenarios
- **Output**: Queue reset logic
- **Dependencies**: T37
- **Status**: ⏳ Pending

---

## M5 - Bot Commands & UX

### T41: Implement /help command
- **Owner**: Bot/UX
- **Duration**: 2 hours
- **Description**:
  - Comprehensive help text in Farsi
  - List all commands with short description
  - Use inline keyboard for navigation if possible
- **Output**: /help command
- **Dependencies**: None
- **Status**: ⏳ Pending

### T42: Implement inline keyboard patterns (one-shot/loop، etc.)
- **Owner**: Bot/UX
- **Duration**: 2 hours
- **Description**:
  - Create helpers for common keyboard patterns
  - Implement selection keyboards
  - Implement confirmation keyboards
  - Test user interaction flow
- **Output**: Keyboard helpers
- **Dependencies**: T05
- **Status**: ⏳ Pending

### T43: Implement /calendar command
- **Owner**: Backend/Bot
- **Duration**: 4 hours
- **Description**:
  - Create src/core/calendar_service.py
  - Gather all plans for target channel
  - Generate 30-day schedule visualization
  - Show past 7 days delivery status
  - Send as text message with week navigation buttons
  - Test with multiple plans
- **Output**: /calendar command
- **Dependencies**: T37, T42
- **Status**: ⏳ Pending

### T44: Implement /logs command
- **Owner**: Backend
- **Duration**: 2 hours
- **Description**:
  - Query logs for a specific plan
  - Show recent error messages، retry attempts، successes
  - Filter by date range if possible
- **Output**: /logs command
- **Dependencies**: T12
- **Status**: ⏳ Pending

### T45: Implement all error messages and confirmations in Farsi
- **Owner**: Bot/UX
- **Duration**: 2 hours
- **Description**:
  - Review all error messages
  - Ensure Farsi text is clear، friendly، helpful
  - Add error codes for debugging
  - Test with various error scenarios
- **Output**: All messages in Farsi
- **Dependencies**: All command tasks
- **Status**: ⏳ Pending

### T46: Implement message state machine (conversation flow)
- **Owner**: Bot
- **Duration**: 2 hours
- **Description**:
  - For commands that span multiple messages، implement state tracking
  - /addroute: track step (ask_source → validate_source → ask_target → validate_target → done)
  - /addplan: track step
  - Store temporary state in Redis or memory
  - Clear state on timeout or completion
- **Output**: State machine for multi-step commands
- **Dependencies**: T42
- **Status**: ⏳ Pending

### T47: Implement rate limiting per user command
- **Owner**: Bot
- **Duration**: 2 hours
- **Description**:
  - Prevent spam commands
  - Allow 1 /start per day per user
  - Allow 1 /addroute per minute per user
  - Send "Too fast, please wait" message
- **Output**: Rate limiting middleware
- **Dependencies**: T07
- **Status**: ⏳ Pending

### T48: Implement message formatting and pagination
- **Owner**: Bot/UX
- **Duration**: 2 hours
- **Description**:
  - Handle long messages (pagination)
  - Format lists with proper indentation
  - Use emojis for status (✅، ❌، ⏳) in Farsi-friendly way
  - Test with long route lists، many plans، etc.
- **Output**: Formatting and pagination helpers
- **Dependencies**: T42
- **Status**: ⏳ Pending

### T49: Implement welcome message on first /start
- **Owner**: Bot/UX
- **Duration**: 1 hour
- **Description**:
  - Show welcome message with trial countdown
  - Explain 3 main actions: /addroute، /buy، /help
  - Quick tutorial links
- **Output**: Welcome message template
- **Dependencies**: T07
- **Status**: ⏳ Pending

### T50: Integration testing of all bot commands
- **Owner**: QA
- **Duration**: 3 hours
- **Description**:
  - Test every command in sequence
  - Test error paths
  - Test with real Rubika account
  - Document any issues
- **Output**: Command test report
- **Dependencies**: All command tasks
- **Status**: ⏳ Pending

---

## M6 - Admin Dashboard

### T51: Setup FastAPI admin app structure
- **Owner**: Admin Dev
- **Duration**: 2 hours
- **Description**:
  - Create src/admin/main.py with FastAPI instance
  - Setup CORS، middleware، auth
  - Serve static files (HTML/CSS/JS)
- **Output**: FastAPI admin server
- **Dependencies**: T12
- **Status**: ⏳ Pending

### T52: Create admin dashboard stats API
- **Owner**: Admin
- **Duration**: 3 hours
- **Description**:
  - /admin/stats endpoint
  - Return: user count، active subs، routes، plans، messages forwarded today
  - Add charts data: messages per day (7 days)، subscription distribution
  - Optimize queries with COUNT، GROUP BY
- **Output**: Stats API with data
- **Dependencies**: T51
- **Status**: ⏳ Pending

### T53: Create admin users management API
- **Owner**: Admin
- **Duration**: 3 hours
- **Description**:
  - /admin/users (GET) - list with pagination، search، filter
  - /admin/users/{user_id} (GET) - details
  - /admin/users/{user_id}/message (POST) - send message
  - /admin/users/{user_id}/extend-subscription (POST) - extend days
  - /admin/users/{user_id}/disable (POST) - disable user
- **Output**: Users management API
- **Dependencies**: T51، T12
- **Status**: ⏳ Pending

### T54: Create admin logs API
- **Owner**: Admin
- **Duration**: 2 hours
- **Description**:
  - /admin/logs (GET) - searchable logs
  - Filters: date range، user، plan، error level
  - Return formatted log entries
  - Test with various filters
- **Output**: Logs API
- **Dependencies**: T51
- **Status**: ⏳ Pending

### T55: Create admin performance metrics API
- **Owner**: Admin
- **Duration**: 2 hours
- **Description**:
  - /admin/performance (GET)
  - Return: messages sent today، error count، avg response time، queue status
  - Hourly breakdown for 24h
- **Output**: Performance API
- **Dependencies**: T51
- **Status**: ⏳ Pending

### T56: Create admin login page (HTML/CSS/JS)
- **Owner**: Frontend
- **Duration**: 2 hours
- **Description**:
  - Simple login form
  - Username + password fields
  - Submit sends JWT request
  - Store JWT in cookie + localStorage
  - Redirect on success، show error on failure
- **Output**: login.html
- **Dependencies**: T51
- **Status**: ⏳ Pending

### T57: Create admin dashboard HTML (stats page)
- **Owner**: Frontend
- **Duration**: 3 hours
- **Description**:
  - Main dashboard layout with sidebar
  - Display stat cards (user count، active subs، routes، etc.)
  - Embed charts (Chart.js for line/pie charts)
  - Responsive design، dark/light mode optional
- **Output**: dashboard.html + chart rendering
- **Dependencies**: T56، T52
- **Status**: ⏳ Pending

### T58: Create admin users table page
- **Owner**: Frontend
- **Duration**: 3 hours
- **Description**:
  - DataTable with users، searchable/filterable
  - Columns: user_id، username، subscription، trial end، active routes، last activity
  - Action buttons: message، extend، disable، view details
  - Implement modal for sending message
  - Test pagination and search
- **Output**: users.html + DataTable integration
- **Dependencies**: T56، T53
- **Status**: ⏳ Pending

### T59: Create admin logs page
- **Owner**: Frontend
- **Duration**: 2 hours
- **Description**:
  - Logs table with filters (date، user، plan، level)
  - Show recent logs first
  - Format error messages nicely
  - Test with various filters
- **Output**: logs.html
- **Dependencies**: T56، T54
- **Status**: ⏳ Pending

### T60: Create admin performance page
- **Owner**: Frontend
- **Duration**: 2 hours
- **Description**:
  - Display metrics: messages/day، errors/day، queue status
  - Hourly breakdown chart (24h)
  - Server health status
- **Output**: performance.html
- **Dependencies**: T56، T55
- **Status**: ⏳ Pending

### T61: Create admin settings page (system)
- **Owner**: Admin
- **Duration**: 2 hours
- **Description**:
  - Bot token validation
  - Trial enable/disable toggle
  - Trial duration settings
  - Webhook URL configuration
  - Save changes to .env / DB
- **Output**: settings.html + API endpoints
- **Dependencies**: T56
- **Status**: ⏳ Pending

### T62: Integration testing of admin dashboard
- **Owner**: QA
- **Duration**: 3 hours
- **Description**:
  - Test login، logout، session expiry
  - Test all pages load correctly
  - Test filtering، searching، pagination
  - Test sending message to user
  - Document any issues
- **Output**: Admin dashboard test report
- **Dependencies**: All admin tasks
- **Status**: ⏳ Pending

---

## M7 - Testing & QA

### T63: Setup pytest and test fixtures
- **Owner**: QA
- **Duration**: 2 hours
- **Description**:
  - Create tests/conftest.py with fixtures (db، client، user)
  - Setup test database (separate from production)
  - Create test user factory
  - Document testing guide
- **Output**: Test infrastructure
- **Dependencies**: T02
- **Status**: ⏳ Pending

### T64: Write unit tests for user service
- **Owner**: QA
- **Duration**: 2 hours
- **Description**:
  - Test get_or_create_user()
  - Test trial creation and expiration
  - Test subscription validation
  - Aim for 80%+ coverage
- **Output**: test_user_service.py
- **Dependencies**: T63، T06
- **Status**: ⏳ Pending

### T65: Write unit tests for route and queue services
- **Owner**: QA
- **Duration**: 3 hours
- **Description**:
  - Test route creation with permission check
  - Test queue operations (add، get next، mark sent/failed)
  - Test sync and update operations
  - Mock Rubika API calls
- **Output**: test_route_service.py، test_queue_service.py
- **Dependencies**: T63، T20، T27
- **Status**: ⏳ Pending

### T66: Write unit tests for schedule service
- **Owner**: QA
- **Duration**: 2 hours
- **Description**:
  - Test plan creation (interval and daily count)
  - Test next_run calculation
  - Test loop_mode behavior
  - Test edge cases (midnight، end of month)
- **Output**: test_schedule_service.py
- **Dependencies**: T63، T29
- **Status**: ⏳ Pending

### T67: Write integration tests for execution engine
- **Owner**: QA
- **Duration**: 4 hours
- **Description**:
  - Test full execution flow: get plan → get post → forward → update
  - Test retry logic with failure scenarios
  - Test queue reset for loop_mode
  - Test plan deactivation on critical errors
  - Simulate multiple plans in parallel
- **Output**: test_execution_engine.py
- **Dependencies**: T63، T37
- **Status**: ⏳ Pending

### T68: Write integration tests for payment flow
- **Owner**: QA
- **Duration**: 3 hours
- **Description**:
  - Test /buy command flow
  - Mock Zarinpal API responses
  - Test polling verification
  - Test subscription activation
  - Test route limit enforcement
- **Output**: test_payment_flow.py
- **Dependencies**: T63، T13
- **Status**: ⏳ Pending

### T69: Write end-to-end tests (bot commands)
- **Owner**: QA
- **Duration**: 3 hours
- **Description**:
  - Simulate complete user journey
  - /start → /addroute → /addplan → execution → /calendar
  - Test error paths
  - Use real or sandbox Rubika account
- **Output**: test_e2e_bot.py
- **Dependencies**: T63، All commands
- **Status**: ⏳ Pending

### T70: Performance and load testing
- **Owner**: QA/DevOps
- **Duration**: 2 hours
- **Description**:
  - Test with 500 concurrent users (simulation)
  - Test with 5000 active plans
  - Monitor memory، CPU، DB connections
  - Identify bottlenecks
  - Document results
- **Output**: Performance test report
- **Dependencies**: T37
- **Status**: ⏳ Pending

---

## M8 - Deployment & Launch

### T71: Create Docker production build
- **Owner**: DevOps
- **Duration**: 2 hours
- **Description**:
  - Multi-stage Dockerfile
  - Non-root user for security
  - Health check endpoint
  - Optimize image size
- **Output**: Production Dockerfile
- **Dependencies**: T05
- **Status**: ⏳ Pending

### T72: Setup systemd service files
- **Owner**: DevOps
- **Duration**: 1 hour
- **Description**:
  - Create rubifo-bot.service
  - Auto-restart on failure
  - Log rotation setup
- **Output**: .service files
- **Dependencies**: None
- **Status**: ⏳ Pending

### T73: Create deployment documentation
- **Owner**: DevOps
- **Duration**: 2 hours
- **Description**:
  - Local development setup guide
  - Staging deployment guide
  - Production deployment guide
  - Database migration steps
  - Rollback procedure
- **Output**: DEPLOYMENT.md
- **Dependencies**: All
- **Status**: ⏳ Pending

### T74: Setup monitoring and alerting (logs)
- **Owner**: DevOps
- **Duration**: 2 hours
- **Description**:
  - Setup log rotation with logrotate
  - Configure logging to file + stdout
  - Setup basic alerting for errors (tail check or Sentry)
- **Output**: Logging configuration
- **Dependencies**: T72
- **Status**: ⏳ Pending

### T75: Launch staging and production
- **Owner**: DevOps
- **Duration**: 2 hours
- **Description**:
  - Deploy to staging environment
  - Run smoke tests
  - Deploy to production
  - Monitor for errors
  - Announce availability
- **Output**: Both environments live
- **Dependencies**: T71، T73
- **Status**: ⏳ Pending

---

## خلاصه WBS

- **Total Tasks**: 75
- **Total Duration**: ~25-27 days (parallel work)
- **Critical Path**: M0 → M1 → M3 → M4 → M5 → M6 → M7 → M8
- **Parallelizable**: M2 and M6 can start early after M1

---

## نتیجه‌گیری P7

✅ تمام 75 task تعریف شده‌اند  
✅ وابستگی‌ها مشخص هستند  
✅ مدت‌های تخمینی واقع‌بینانه هستند  
✅ Milestones هفتگی سازماندهی شده‌اند  

**مراحل بعدی:**  
- P8: دستورالعمل‌های AI (CLAUDE.md، AGENTS.md)
- P9: چک‌لیست‌های deployment و محتوا
- شروع اجرا از T01

