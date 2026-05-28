# 🎯 Implementation Prompt for Sonnet 4.6
**Rubifo Bot UI Redesign - Destination-Centric Architecture**

---

## 📋 Context

You are implementing a major UI redesign for Rubifo (Rubika bot for content forwarding).

**Reference Design:** `docs/superpowers/specs/2026-05-19-bot-ui-redesign.md`

**Official Rubika API Docs:**
- Methods: https://rubika.ir/botapi/methods
- Models: https://rubika.ir/botapi/models
- Group/Channel: https://rubika.ir/botapi/group-channel

**Project Guidelines:** `CLAUDE.md` (all rules apply)

---

## 🎯 Objective

Transform the bot's UI from a flat 8-button keypad into a **Destination-Centric** model where:
1. **Keypad:** 7 buttons (3x2+1) organized by frequency of use
2. **Inline buttons:** Context-sensitive actions under each message
3. **Destination channels:** Foundation of the data model (limited by tier)
4. **Daily workflow:** Calendar → Sources → Add Posts → Plans

**Non-Goal:** Do NOT change database schema. Logic changes only.

---

## 🔑 Key Principles

### 1. Destination Channel Limits
- **Limit is on CHANNELS, not routes**
- Basic: 1 destination channel (can have unlimited routes/plans to it)
- Pro: 3 destination channels
- Enterprise: 10 destination channels
- Validation: `can_create_route()` must check **distinct `target_channel_id` count**, not route count

### 2. Setup vs Daily
- **Setup (one-time):** User verifies destination channels via admin check
- **After:** Channels are trusted; daily workflow focuses on content
- No re-verification for setup actions

### 3. Inline Buttons (per Rubika API)
- Use `send_message()` with **native Rubika keypad buttons**
- Per https://rubika.ir/botapi/models → Keypad structure
- Each message can have multiple button rows
- Button `type`: SIMPLE (text-only, no callback)
- Button `button_text`: emoji + farsi text

### 4. Conversation State
- Existing `conversation_states` dict stays; don't refactor
- New commands use the same pattern

---

## 🏗️ Implementation Structure

### Phase 1: Core Changes (Priority 1)

#### File: `src/bot/main.py`
**Change:** Redefine `MAIN_KEYPAD`

```python
MAIN_KEYPAD = Keypad(rows=[
    KeypadRow(buttons=[
        Button(id="mysources", type=ButtonTypeEnum.SIMPLE, button_text="📦 سورس‌های من"),
        Button(id="my_destinations", type=ButtonTypeEnum.SIMPLE, button_text="📍 کانال‌های من"),
        Button(id="listroutes", type=ButtonTypeEnum.SIMPLE, button_text="📋 مسیرهای من"),
    ]),
    KeypadRow(buttons=[
        Button(id="listplans", type=ButtonTypeEnum.SIMPLE, button_text="📅 پلن‌های من"),
        Button(id="calendar", type=ButtonTypeEnum.SIMPLE, button_text="📊 تقویم محتوایی"),
        Button(id="subscription_status", type=ButtonTypeEnum.SIMPLE, button_text="💳 اشتراک"),
    ]),
    KeypadRow(buttons=[
        Button(id="help", type=ButtonTypeEnum.SIMPLE, button_text="❓ راهنما"),
    ]),
])
```

**Remove:** 
- `button_text="✏️ سورس جدید"` (move to inline in `/mysources`)
- `button_text="➕ مسیر جدید"` (move to inline in `/my_destinations`)
- `button_text="💳 خرید اشتراک"` (merge into `/subscription_status`)

---

#### File: `src/bot/commands.py`

**New Functions:**

##### 1. `handle_my_destinations()`
```
Purpose: List all destination channels with per-destination hub
Input: client, user_id
Output: Message showing:
  - List of verified destination channels
  - For each: routes, plans, calendar, add-route buttons
  - Display used/limit (e.g., "2/3 کانال‌های شما")

Logic:
1. Query: SELECT DISTINCT target_channel_id FROM routes WHERE user_id = $1
2. Get subscription tier → find limits (1/3/10)
3. For each channel:
   a. Count routes to this channel
   b. Count plans to routes of this channel
   c. Count pending posts in queue for routes of this channel
   d. Generate inline buttons:
      - [نمایش مسیرها] → list routes
      - [نمایش پلن‌ها] → list plans
      - [مشاهده تقویم] → calendar for this channel
      - [➕ مسیر جدید] → addroute flow for this channel
      - [🗑️ حذف] → delete channel (cascade routes)
5. At bottom: [✏️ کانال جدید] if under limit
```

**Implementation Notes:**
- Use Keypad with multiple ButtonRows for each channel
- Each row = one channel + 2-3 buttons
- Inline buttons use `aux_data` and `button_id` (per Rubika API)

---

##### 2. `handle_subscription_status()`
```
Purpose: Show subscription status, days left, usage, renew/upgrade options
Input: client, user_id
Output: Message showing:
  - Current tier (Basic/Pro/Enterprise)
  - Days left
  - Destinations used/limit (e.g., "2/3")
  - List verified channels
  - [🔄 تمدید] [⬆️ ارتقا] buttons

Logic:
1. Query subscription: SELECT tier, end_date FROM subscriptions WHERE user_id = $1
2. Get destinations: SELECT COUNT(DISTINCT target_channel_id) FROM routes WHERE user_id = $1
3. Get tier limit: SUBSCRIPTION_TIERS[tier]["destination_channels"]
4. Calculate: days_left = (end_date - now()).days
5. Format message with clear usage visualization
6. Inline buttons for renew (✅ active) or buy (❌ expired)
```

**Implementation Notes:**
- Replace current `/buy` endpoint logic for status
- Keep `/buy_basic`, `/buy_pro`, `/buy_enterprise` for checkout
- Show trial status separately (hours left)

---

##### 3. `handle_calendar()` — MODIFY
```
Current: /calendar [channel_id]
New: /calendar (interactive channel selection)

Logic:
1. Get user's destination channels
2. If zero: "تاکنون کانال تعریف نکردید. /my_destinations"
3. If one: Show calendar directly for that channel
4. If multiple: 
   a. Send message: "کدوم کانال؟"
   b. Add inline buttons: [1️⃣ @channel_A] [2️⃣ @channel_B] ...
   c. Set conversation_state: command="calendar_select", channels={}
   d. route_message() handles button click → calls handle_calendar_display()
```

**Implementation Notes:**
- Button numbering (1️⃣ 2️⃣ 3️⃣) is visual only
- Button `button_id` is the channel name (e.g., "channel_a")
- Async fetch calendar data for 30 days

---

##### 4. `handle_calendar_display()` — NEW
```
Purpose: Display 30-day calendar for selected destination channel
Input: client, user_id, target_channel_id
Output: Calendar with:
  - Week navigation [◀️ هفته قبل] [هفته بعد ▶️]
  - Each day: time, route source name, plan type
  - Inline buttons: [📝 مسیرهای این کانال] [➕ مسیر جدید]

Logic:
1. Query schedules for all routes to this channel
2. For next 30 days, calculate next_run for each schedule
3. Format as:
   ```
   شنبه ۲۵ اردیبهشت:
   ۰۸:۰۰ — تبلیغات (Plan #1)
   ۱۰:۳۰ — خبرها (Plan #2)
   ```
4. Week navigation via conversation_state

**Implementation Notes:**
- Use `fmt_tehran()` for date formatting
- Show plan type: interval, daily_count, campaign, etc.
- If empty week: "هیچ برنامه ای برای این هفته نیست"
```

---

##### 5. `handle_mysources()` — MODIFY
```
Current: Shows sources with /viewsource, /addpost, /deletesource buttons
New: Add inline button [➕ افزودن پست] for each source

Logic:
1. List sources as before
2. For each source, add inline row:
   [مشاهده پست‌ها] [➕ افزودن پست] [✏️ ویرایش]
3. Button IDs: "viewsource_X", "addpost_X", "editsource_X"
4. At bottom: [✏️ سورس جدید]

Implementation Notes:**
- `/addpost` is now inline; no `/addpost [id]` in keypad
- Button click with `button_id="addpost_X"` → handle_addpost_inline()
- Maintain backward compatibility: `/addpost 5` still works
```

---

#### File: `src/bot/handlers.py`

**Changes:**

1. Add to `BUTTON_COMMAND_MAP`:
```python
BUTTON_COMMAND_MAP = {
    # ... existing ...
    "📍 کانال‌های من": "/my_destinations",
    "💳 اشتراک": "/subscription_status",
    # Remove: "💳 خرید اشتراک" → merged into /subscription_status
    # Remove: "✏️ سورس جدید" → inline in /mysources
    # Remove: "➕ مسیر جدید" → inline in /my_destinations
}
```

2. Add command dispatch:
```python
elif cmd == "/my_destinations":
    await commands.handle_my_destinations(client, user_id)
elif cmd == "/subscription_status":
    await commands.handle_subscription_status(client, user_id)
```

3. Add inline button handling:
```python
# In route_message(), after BUTTON_COMMAND_MAP check:
if text.startswith("/"):
    # Extract button_id from text
    btn_id = text.lstrip("/")
    
    # Route inline buttons
    if btn_id.startswith("viewsource_"):
        source_id = int(btn_id.split("_")[1])
        await commands.handle_viewsource(client, user_id, source_id)
    elif btn_id.startswith("addpost_"):
        source_id = int(btn_id.split("_")[1])
        await commands.handle_addpost(client, user_id, source_id)
    # ... etc
```

---

#### File: `src/core/route_service.py`

**Modify: `can_create_route()`**

```python
async def can_create_route(self, user_id: str, target_channel_id: str) -> Tuple[bool, str]:
    """
    Check if user can create a route to target_channel_id.
    
    Limit is on DISTINCT destination channels, not total routes.
    E.g., Basic tier = 1 unique destination channel (can have unlimited routes to it).
    """
    # Get subscription tier
    sub = await SubscriptionService(self.pool).get_active_subscription(user_id)
    if not sub:
        return False, "❌ اشتراک فعالی ندارید. /buy برای خرید."
    
    tier = sub.tier
    max_destinations = SUBSCRIPTION_TIERS.get(tier, {}).get("destination_channels", 1)
    
    # Count DISTINCT destination channels user already has
    row = await self.pool.fetchrow(
        """
        SELECT COUNT(DISTINCT target_channel_id) as count
        FROM routes
        WHERE user_id = $1 AND is_active = true
        """,
        user_id
    )
    current_destinations = row["count"] if row else 0
    
    # Check if target_channel already registered
    existing_route = await self.pool.fetchrow(
        "SELECT id FROM routes WHERE user_id = $1 AND target_channel_id = $2 AND is_active = true LIMIT 1",
        user_id, target_channel_id
    )
    
    if existing_route:
        # Same destination allowed (unlimited routes to same destination)
        return True, ""
    
    if current_destinations >= max_destinations:
        # Limit reached
        return False, (
            f"❌ محدودیت پلن {_tier_name(tier)}:\n\n"
            f"شما فقط {max_destinations} کانال مقصد می‌توانید داشته باشید.\n\n"
            f"برای اضافه کردن {target_channel_id}:\n"
            f"[⬆️ ارتقا به Pro] (۳ کانال)\n"
            f"[⬆️ ارتقا به Enterprise] (۱۰ کانال)"
        )
    
    return True, ""
```

**New Functions:**

```python
async def get_destinations_by_user(self, user_id: str) -> List[Dict]:
    """Get all verified destination channels for a user."""
    return await self.pool.fetch(
        """
        SELECT DISTINCT target_channel_id
        FROM routes
        WHERE user_id = $1 AND is_active = true
        ORDER BY target_channel_id
        """,
        user_id
    )

async def get_destination_stats(self, user_id: str, target_channel_id: str) -> Dict:
    """Get stats for a destination: routes, plans, pending posts."""
    routes = await self.pool.fetch(
        "SELECT id FROM routes WHERE user_id = $1 AND target_channel_id = $2 AND is_active = true",
        user_id, target_channel_id
    )
    
    plans = await self.pool.fetch(
        """
        SELECT id FROM schedules
        WHERE route_id = ANY($1) AND is_active = true
        """,
        [r["id"] for r in routes]
    )
    
    pending = await self.pool.fetchval(
        """
        SELECT COUNT(*) FROM post_queue pq
        JOIN routes r ON pq.route_id = r.id
        WHERE r.user_id = $1 AND r.target_channel_id = $2 AND pq.status = 'pending'
        """,
        user_id, target_channel_id
    )
    
    return {
        "target_channel_id": target_channel_id,
        "route_count": len(routes),
        "plan_count": len(plans),
        "pending_posts": pending or 0,
    }
```

---

#### File: `src/core/subscription_service.py`

**New Function:**

```python
async def get_subscription_status(self, user_id: str) -> Dict:
    """Return subscription status for display."""
    from datetime import datetime
    
    sub = await self.get_active_subscription(user_id)
    user = await UserService(self.pool).get_user(user_id)
    
    if not sub and user and user.is_trial_active:
        # Trial mode
        hours_left = max(0, (user.trial_end_at - datetime.now()).total_seconds() / 3600)
        destinations_used = await self.pool.fetchval(
            "SELECT COUNT(DISTINCT target_channel_id) FROM routes WHERE user_id = $1",
            user_id
        )
        return {
            "status": "trial",
            "tier": None,
            "end_date": user.trial_end_at,
            "hours_left": hours_left,
            "days_left": int(hours_left / 24),
            "destinations_used": destinations_used or 0,
            "destinations_limit": 1,  # Trial: 1 channel
        }
    elif sub:
        # Active subscription
        days_left = (sub.end_date - datetime.now().date()).days
        destinations_used = await self.pool.fetchval(
            "SELECT COUNT(DISTINCT target_channel_id) FROM routes WHERE user_id = $1",
            user_id
        )
        tier_limit = SUBSCRIPTION_TIERS.get(sub.tier, {}).get("destination_channels", 1)
        return {
            "status": "active",
            "tier": sub.tier,
            "end_date": sub.end_date,
            "days_left": max(0, days_left),
            "destinations_used": destinations_used or 0,
            "destinations_limit": tier_limit,
        }
    else:
        # Expired
        return {
            "status": "expired",
            "tier": None,
            "end_date": None,
            "days_left": 0,
            "destinations_used": 0,
            "destinations_limit": 0,
        }
```

---

### Phase 2: Command Routing Updates

#### File: `src/bot/handlers.py` — Add conversation routes

```python
elif state.get("command") == "calendar_select":
    await handle_calendar_select_response(client, user_id, text)
elif state.get("command") == "my_destinations_create":
    await handle_my_destinations_create_response(client, user_id, text)
```

---

### Phase 3: Inline Button Implementation

**Use Rubika Keypad structure per API docs:**

```python
def _make_inline_buttons(buttons: List[Tuple[str, str]]) -> Keypad:
    """
    Convert list of (label, button_id) to Keypad.
    Example:
      [("مشاهده پست‌ها", "viewsource_1"), ("➕ افزودن", "addpost_1")]
    """
    rows = []
    for i in range(0, len(buttons), 2):
        button_list = []
        for label, btn_id in buttons[i:i+2]:
            button_list.append(
                Button(id=btn_id, type=ButtonTypeEnum.SIMPLE, button_text=label)
            )
        rows.append(KeypadRow(buttons=button_list))
    return Keypad(rows=rows)
```

---

## ✅ Testing Checklist

### Unit Tests
```python
# Test: Destination limit validation
async def test_destination_limit_basic():
    user = await get_user_for_test(tier="basic")
    
    # First channel should succeed
    ok, msg = await RouteService(pool).can_create_route(user.user_id, "@channel_a")
    assert ok == True
    
    # Same channel, different source should succeed
    ok, msg = await RouteService(pool).can_create_route(user.user_id, "@channel_a")
    assert ok == True
    
    # Different channel should fail
    ok, msg = await RouteService(pool).can_create_route(user.user_id, "@channel_b")
    assert ok == False
    assert "محدودیت پلن" in msg

# Test: Subscription status
async def test_subscription_status():
    user = await create_test_user()
    sub = await SubscriptionService(pool).get_subscription_status(user.user_id)
    
    assert sub["status"] == "trial"
    assert sub["destinations_limit"] == 1
```

### Integration Tests
```python
# Test: /my_destinations shows only unique channels
async def test_my_destinations():
    user = await create_test_user()
    # Create 2 routes to same channel
    await RouteService(pool).create_route(user.user_id, source_1, "@channel_a")
    await RouteService(pool).create_route(user.user_id, source_2, "@channel_a")
    
    # /my_destinations should show @channel_a ONCE
    # with 2 routes listed
    
# Test: Calendar selection workflow
async def test_calendar_workflow():
    # Send /calendar
    # User selects @channel_a
    # Calendar displays for that channel
```

---

## 🚀 Deployment Checklist

- [ ] All new functions follow CLAUDE.md guidelines (type hints, docstrings, error handling)
- [ ] No hardcoded values (use config)
- [ ] Logging added for all major flows
- [ ] Destination limit validation in `can_create_route()` is correct
- [ ] Inline buttons use correct Rubika API format
- [ ] Backward compatibility: old `/addpost 5` still works
- [ ] Conversation state cleanup on success
- [ ] Error messages in Farsi
- [ ] Tested with 0 channels, 1 channel, multiple channels
- [ ] Tested with trial, active, and expired subscriptions
- [ ] Database queries use parameterized inputs (no SQL injection)

---

## 🎯 Success Criteria

✅ Keypad has exactly 7 buttons (3x2+1)  
✅ Inline buttons appear under messages (not in keypad)  
✅ `/my_destinations` shows unique channels with stats  
✅ `/subscription_status` shows clear usage (X/Y channels)  
✅ `/calendar` allows channel selection, displays 30-day view  
✅ Destination limit check is on DISTINCT channels, not routes  
✅ All commands preserve conversation state for multi-step flows  
✅ Tests pass for single, multiple, and tier-limited scenarios  
✅ No schema changes required  

---

## 📚 References

**Design Spec:**
- `docs/superpowers/specs/2026-05-19-bot-ui-redesign.md`

**Rubika API:**
- https://rubika.ir/botapi/methods
- https://rubika.ir/botapi/models
- https://rubika.ir/botapi/group-channel

**Project Rules:**
- `CLAUDE.md` (all guidelines apply)
- `P5-user-journey-and-scope.md` (user flows context)

---

## 🔍 Code Review Checklist (for reviewer)

- [ ] All new functions in commands.py have async/await
- [ ] Type hints complete (no `Any` unless necessary)
- [ ] Docstrings explain PURPOSE, not WHAT (no "returns a list")
- [ ] Error messages are user-friendly (Farsi)
- [ ] Database queries use `$1, $2` parameterized format
- [ ] No global state (use dependency injection)
- [ ] Inline buttons use correct Keypad structure
- [ ] Destination limit logic is correct (DISTINCT channels)
- [ ] Conversation state is cleaned up after success
- [ ] Logging at INFO level for normal flow, ERROR for exceptions

---

**End of Implementation Prompt**

This prompt is ready to hand to another Sonnet instance for flawless implementation.
