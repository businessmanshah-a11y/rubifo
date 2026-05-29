"""User-facing wizard for creating automated publishing programs."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.core.destination_service import DestinationService
from src.core.professional_schedule import PublishingProgramConfig, describe_plan, format_hhmm
from src.core.publishing_program_service import PublishingProgramService
from src.core.source_service import SourceService, _detect_message_type
from src.logger import logger


active_flows: Dict[str, Dict[str, Any]] = {}

TUTORIAL = "🧪 برنامه آزمایشی و آموزشی"
REAL = "🚀 برنامه واقعی"
NEW_CATEGORY = "➕ ساخت دسته محتوای جدید"
EXISTING_CATEGORY = "📁 انتخاب از دسته‌های قبلی"
RECURRING = "انتشار منظم روزانه"
DATED = "کمپین تاریخ‌دار"
GUIDE = "راهنمای چیدمان محتوا"
INTERVAL = "فاصله ثابت"
DAILY_COUNT = "تعداد روزانه"
EXACT_TIMES = "ساعت‌های دقیق"
SAVE_CATEGORY = "ذخیره دسته و ادامه"
CONFIRM = "تایید برنامه"


def _inline_choices(*labels: str):
    from rubpy.bot.enums import ButtonTypeEnum
    from rubpy.bot.models import Button, Keypad, KeypadRow

    return Keypad(
        rows=[
            KeypadRow(buttons=[Button(id=label, type=ButtonTypeEnum.SIMPLE, button_text=label)])
            for label in labels
        ]
    )


async def _persist(user_id: str, state: Dict[str, Any]) -> None:
    from src.database import pool

    destination = state.get("destination")
    source = state.get("source")
    payload = {
        key: value
        for key, value in state.items()
        if key not in {"destination", "source", "source_map", "step", "flow_kind"}
        and isinstance(value, (str, int, float, bool, list, dict, type(None)))
    }
    await PublishingProgramService(pool).save_draft(
        user_id,
        state.get("flow_kind", "real"),
        state["step"],
        getattr(destination, "id", state.get("destination_id", None)),
        getattr(source, "id", state.get("source_id", None)),
        payload,
    )


async def begin_program(client, user_id: str, restart: bool = False) -> None:
    from src.database import pool

    service = PublishingProgramService(pool)
    if restart:
        await service.clear_draft(user_id)
    else:
        draft = await service.get_draft(user_id)
        if draft:
            active_flows[user_id] = {"step": "resume", "draft": draft}
            await client.send_message(
                user_id,
                "یک برنامه انتشار نیمه‌کاره دارید.\n\n"
                "برای ادامه «ادامه ساخت» و برای حذف آن «شروع دوباره» را انتخاب کنید.",
                inline_keypad=_inline_choices("ادامه ساخت", "شروع دوباره"),
            )
            return
    active_flows[user_id] = {"step": "choose_kind"}
    await client.send_message(
        user_id,
        "می‌خواهید چطور شروع کنید؟\n\n"
        f"{TUTORIAL}\n"
        f"{REAL}",
        inline_keypad=_inline_choices(TUTORIAL, REAL),
    )


async def begin_real_program(client, user_id: str) -> None:
    """Start the real flow after cleaning the temporary tutorial artifacts."""
    from src.database import pool

    service = PublishingProgramService(pool)
    await service.cleanup_tutorial(user_id)
    state = {"step": "channel", "flow_kind": "real"}
    active_flows[user_id] = state
    await _persist(user_id, state)
    await client.send_message(
        user_id,
        "داده‌های آزمایش پاک شدند. پست‌هایی که در کانال منتشر شده‌اند حذف نمی‌شوند "
        "و باید داخل کانال حذف شوند.",
    )
    await _prompt_channel(client, user_id, state)


async def begin_edit_program(client, user_id: str, schedule_id: int) -> None:
    """Edit a real publishing schedule without exposing its internal route."""
    from src.database import pool

    service = PublishingProgramService(pool)
    components = await service.get_program_components(user_id, schedule_id)
    if not components:
        await client.send_message(user_id, "❌ برنامه انتشار یافت نشد.")
        return
    destination, source = components
    state = {
        "step": "purpose",
        "flow_kind": "real",
        "edit_schedule_id": schedule_id,
        "destination": destination,
        "source": source,
    }
    active_flows[user_id] = state
    await _persist(user_id, state)
    await client.send_message(user_id, f"ویرایش زمان‌بندی برنامه «{source.name}»")
    await _prompt_purpose(client, user_id)


async def _restore_draft(user_id: str, draft) -> Dict[str, Any]:
    from src.database import pool

    state = {"step": draft.step, "flow_kind": draft.flow_kind, **(draft.payload or {})}
    if draft.destination_id:
        state["destination"] = await DestinationService(pool).get(draft.destination_id, user_id)
    if draft.source_id:
        state["source"] = await SourceService(pool).get_source(draft.source_id)
    active_flows[user_id] = state
    return state


async def _prompt_channel(client, user_id: str, state: Dict[str, Any]) -> None:
    from src.database import pool

    channels = await DestinationService(pool).list_verified(user_id)
    known = ""
    if channels:
        known = "\nکانال‌های تاییدشده شما:\n" + "\n".join(
            f"{index}. {channel.channel_id}" for index, channel in enumerate(channels, 1)
        )
    await client.send_message(
        user_id,
        "کانال مقصد همان جایی است که پست‌ها منتشر می‌شوند.\n"
        "ابتدا Rubifo را در آن کانال ادمین کنید و اجازه ارسال پست بدهید.\n"
        "سپس یکی از این‌ها را بفرستید:\n"
        "@my_channel\n"
        "https://rubika.ir/my_channel\n"
        "یا یک پست فورواردشده از همان کانال."
        f"{known}\n\nبعد از رفع خطا، آدرس کانال یا پست فورواردشده را دوباره ارسال کنید.",
        inline_keypad=_inline_choices(*[channel.channel_id for channel in channels]) if channels else None,
    )


def _forwarded_channel_identifier(message: Optional[Dict[str, Any]]) -> Optional[str]:
    if not message:
        return None
    new_message = message.get("new_message") if isinstance(message, dict) else None
    forwarded = (new_message or {}).get("forwarded_from") or {}
    identifier = forwarded.get("chat_id") or forwarded.get("object_guid")
    return str(identifier).strip() if identifier else None


async def handle_text(client, user_id: str, text: str, message: Optional[Dict[str, Any]] = None) -> bool:
    """Consume wizard text and return whether the message belonged to the wizard."""
    from src.database import pool

    state = active_flows.get(user_id)
    if not state:
        return False
    value = text.strip()
    service = PublishingProgramService(pool)

    try:
        if state["step"] == "resume":
            if value == "شروع دوباره":
                await begin_program(client, user_id, restart=True)
                return True
            if value != "ادامه ساخت":
                await client.send_message(user_id, "«ادامه ساخت» یا «شروع دوباره» را انتخاب کنید.")
                return True
            state = await _restore_draft(user_id, state["draft"])
            await _repeat_step_prompt(client, user_id, state)
            return True

        if state["step"] == "choose_kind":
            if value not in (TUTORIAL, REAL):
                await client.send_message(user_id, f"یکی از دو گزینه را انتخاب کنید:\n{TUTORIAL}\n{REAL}")
                return True
            flow_kind = "tutorial" if value == TUTORIAL else "real"
            if flow_kind == "tutorial":
                allowed, reason = await service.can_create_tutorial(user_id)
                if not allowed:
                    await client.send_message(user_id, f"{reason}\nارتقای اشتراک: /buy")
                    return True
            if flow_kind == "real":
                await service.cleanup_tutorial(user_id)
            state.update({"flow_kind": flow_kind, "step": "channel"})
            await _persist(user_id, state)
            if flow_kind == "tutorial":
                await client.send_message(
                    user_id,
                    "در آزمایش، سه پست واقعاً در کانال انتخابی منتشر می‌شوند.\n"
                    "اگر کانال اصلی حساس است، یک کانال آزمایشی معرفی کنید.",
                )
            await _prompt_channel(client, user_id, state)
            return True

        if state["step"] == "channel":
            forwarded_channel_id = _forwarded_channel_identifier(message)
            try:
                channel_id = forwarded_channel_id or DestinationService.normalize_channel_input(value)
            except ValueError as exc:
                await client.send_message(user_id, str(exc))
                return True
            allowed, error = await DestinationService(pool).can_register(user_id, channel_id)
            if not allowed:
                state.update({"step": "channel_limit", "pending_channel_id": channel_id})
                await _persist(user_id, state)
                await client.send_message(
                    user_id,
                    f"{error}\n\n"
                    "یکی از این اقدام‌ها را انتخاب کنید:\n"
                    "ادامه با کانال ثبت‌شده\n"
                    "جایگزینی کانال\n"
                    "ارتقای اشتراک",
                    inline_keypad=_inline_choices(
                        "ادامه با کانال ثبت‌شده", "جایگزینی کانال", "ارتقای اشتراک"
                    ),
                )
                return True
            verification = await client.verify_destination_channel(channel_id)
            status = verification["status"]
            if not verification.get("verified"):
                instructions = {
                    "not_admin": "Rubifo هنوز ادمین کانال نیست. آن را ادمین کنید، اجازه ارسال پست بدهید، سپس دوباره آدرس یا یک پست فورواردشده از کانال را بفرستید.",
                    "invalid_access": "Rubifo به این آدرس دسترسی ندارد. یک پست از همان کانال را فوروارد کنید تا شناسه واقعی کانال بررسی شود.",
                    "invalid_input": "آدرس کانال معتبر نیست. آیدی را مثل @my_channel یا لینک rubika.ir بفرستید.",
                    "cannot_publish": "Rubifo اجازه انتشار در کانال را ندارد. دسترسی ارسال پست را فعال کنید و دوباره بررسی کنید.",
                    "not_found": "آدرس کانال پیدا نشد؛ آدرس را بررسی و دوباره ارسال کنید.",
                    "api_error": "روبیکا پاسخ خطا داد. چند دقیقه بعد دوباره آدرس یا یک پست فورواردشده از کانال را بفرستید.",
                }
                await client.send_message(user_id, f"تایید کانال انجام نشد.\n{instructions.get(status, 'تلاش مجدد کنید.')}")
                return True
            verified_channel_id = verification.get("channel_id") or channel_id
            destination = await DestinationService(pool).record_verification(
                user_id,
                verified_channel_id,
                verification.get("title"),
                status,
                verification.get("error"),
            )
            state["destination"] = destination
            if status == "cleanup_failed":
                await client.send_message(
                    user_id, "کانال تایید شد، اما پیام بررسی حذف نشد؛ لطفاً آن پیام را داخل کانال حذف کنید."
                )
            if state["flow_kind"] == "tutorial":
                user_row = await pool.fetchrow("SELECT id FROM users WHERE user_id = $1", user_id)
                source = await SourceService(pool).create_source(
                    user_row["id"], "تست اولیه", program_purpose="tutorial_test"
                )
                state.update({"source": source, "step": "tutorial_posts", "post_count": 0})
                await _persist(user_id, state)
                await client.send_message(user_id, "کانال تایید شد. پست ۱ از ۳ را بفرستید.")
            else:
                state["step"] = "content_choice"
                await _persist(user_id, state)
                await _prompt_content_choice(client, user_id)
            return True

        if state["step"] == "channel_limit":
            if value == "ارتقای اشتراک":
                await client.send_message(user_id, "برای افزایش ظرفیت کانال‌ها، اشتراک را ارتقا دهید: /buy")
                return True
            if value == "ادامه با کانال ثبت‌شده":
                state["step"] = "channel"
                await _persist(user_id, state)
                await _prompt_channel(client, user_id, state)
                return True
            if value == "جایگزینی کانال":
                destinations = await DestinationService(pool).list_verified(user_id)
                state["step"] = "replace_channel"
                await _persist(user_id, state)
                listed = "\n".join(destination.channel_id for destination in destinations)
                await client.send_message(
                    user_id,
                    "کانالی را که باید جایگزین شود ارسال کنید:\n" + listed,
                    inline_keypad=_inline_choices(*[destination.channel_id for destination in destinations]),
                )
                return True
            await client.send_message(
                user_id, "«ادامه با کانال ثبت‌شده»، «جایگزینی کانال» یا «ارتقای اشتراک» را انتخاب کنید."
            )
            return True

        if state["step"] == "replace_channel":
            destinations = await DestinationService(pool).list_verified(user_id)
            selected = next((destination for destination in destinations if destination.channel_id == value), None)
            if not selected:
                await client.send_message(user_id, "یکی از کانال‌های ثبت‌شده نمایش‌داده‌شده را ارسال کنید.")
                return True
            dependent = await DestinationService(pool).count_active_programs(user_id, selected.id)
            state["replacement_destination_id"] = selected.id
            if dependent:
                state["step"] = "replace_channel_confirm"
                await _persist(user_id, state)
                await client.send_message(
                    user_id,
                    f"این کانال در {dependent} برنامه فعال استفاده می‌شود. "
                    "با جایگزینی، آن برنامه‌ها متوقف می‌شوند.\n"
                    "برای ادامه «تایید جایگزینی» را بفرستید.",
                    inline_keypad=_inline_choices("تایید جایگزینی"),
                )
                return True
            await DestinationService(pool).replace(user_id, selected.id)
            pending = state.pop("pending_channel_id")
            state["step"] = "channel"
            await _persist(user_id, state)
            return await handle_text(client, user_id, pending)

        if state["step"] == "replace_channel_confirm":
            if value != "تایید جایگزینی":
                await client.send_message(user_id, "برای توقف برنامه‌های وابسته و جایگزینی «تایید جایگزینی» را بفرستید.")
                return True
            await DestinationService(pool).replace(user_id, state["replacement_destination_id"])
            pending = state.pop("pending_channel_id")
            state["step"] = "channel"
            await _persist(user_id, state)
            return await handle_text(client, user_id, pending)

        if state["step"] == "content_choice":
            if value == NEW_CATEGORY:
                state["step"] = "new_category_name"
                await _persist(user_id, state)
                await client.send_message(
                    user_id, "نام دسته محتوا را وارد کنید؛ مثلاً معرفی محصول، آموزشی یا رضایت مشتری."
                )
                return True
            if value == EXISTING_CATEGORY:
                db_uid = await pool.fetchval("SELECT id FROM users WHERE user_id = $1", user_id)
                sources = await SourceService(pool).get_user_sources(db_uid)
                if not sources:
                    await client.send_message(user_id, "دسته قبلی ندارید؛ «➕ ساخت دسته محتوای جدید» را انتخاب کنید.")
                    return True
                state["source_map"] = {str(index): source for index, source in enumerate(sources, 1)}
                state["step"] = "existing_category"
                await _persist(user_id, state)
                lines = [f"{i}. {source.name} ({await SourceService(pool).count_posts(source.id)} پست)" for i, source in enumerate(sources, 1)]
                await client.send_message(
                    user_id,
                    "شماره دسته را انتخاب کنید:\n" + "\n".join(lines),
                    inline_keypad=_inline_choices(*state["source_map"].keys()),
                )
                return True
            await _prompt_content_choice(client, user_id)
            return True

        if state["step"] == "existing_category":
            source = state.get("source_map", {}).get(value)
            if not source:
                await client.send_message(user_id, "شماره دسته معتبر نیست.")
                return True
            if await service.source_has_active_program(source.id):
                state.update({"candidate_source": source, "step": "reuse_warning"})
                await client.send_message(
                    user_id,
                    "این دسته در یک برنامه فعال استفاده می‌شود و ممکن است همان محتوا "
                    "در چند برنامه یا کانال منتشر شود.\n"
                    "برای ادامه «ادامه با همین دسته» و برای بازگشت «انتخاب دسته دیگر» را بفرستید.",
                    inline_keypad=_inline_choices("ادامه با همین دسته", "انتخاب دسته دیگر"),
                )
                return True
            state.update({"source": source, "step": "purpose"})
            await _persist(user_id, state)
            await _prompt_purpose(client, user_id)
            return True

        if state["step"] == "reuse_warning":
            if value == "انتخاب دسته دیگر":
                state["step"] = "content_choice"
                await _persist(user_id, state)
                await _prompt_content_choice(client, user_id)
                return True
            if value != "ادامه با همین دسته":
                await client.send_message(user_id, "«ادامه با همین دسته» یا «انتخاب دسته دیگر» را انتخاب کنید.")
                return True
            state.update({"source": state.pop("candidate_source"), "step": "purpose"})
            await _persist(user_id, state)
            await _prompt_purpose(client, user_id)
            return True

        if state["step"] == "new_category_name":
            name = value[:100].strip()
            if not name:
                await client.send_message(user_id, "نام دسته را وارد کنید.")
                return True
            db_uid = await pool.fetchval("SELECT id FROM users WHERE user_id = $1", user_id)
            source = await SourceService(pool).create_source(db_uid, name)
            state.update({"source": source, "step": "real_posts", "post_count": 0})
            await _persist(user_id, state)
            await client.send_message(
                user_id,
                f"دسته «{name}» ساخته شد. پست‌های مربوط به همین موضوع را بفرستید.\n"
                f"هر زمان آماده بودید «{SAVE_CATEGORY}» را بفرستید؛ دسته خالی هم قابل ذخیره است.",
                inline_keypad=_inline_choices(SAVE_CATEGORY),
            )
            return True

        if state["step"] == "real_posts" and value == SAVE_CATEGORY:
            state["step"] = "purpose"
            await _persist(user_id, state)
            await _prompt_purpose(client, user_id)
            return True

        if state["step"] == "tutorial_interval":
            interval = {"هر ۱ دقیقه - تست سریع": 1, "هر ۵ دقیقه - پیشنهادی": 5, "هر ۱۰ دقیقه": 10}.get(value)
            if not interval:
                await client.send_message(user_id, "یکی از فاصله‌های ۱، ۵ یا ۱۰ دقیقه را انتخاب کنید.")
                return True
            state["interval_minutes"] = interval
            state["step"] = "tutorial_confirm"
            await _persist(user_id, state)
            await client.send_message(
                user_id,
                f"سه پست هر {interval} دقیقه منتشر می‌شوند.\nبرای شروع «{CONFIRM}» را بفرستید.",
                inline_keypad=_inline_choices(CONFIRM),
            )
            return True

        if state["step"] == "tutorial_confirm" and value == CONFIRM:
            await service.commit_tutorial(user_id, state["destination"], state["source"], state["interval_minutes"])
            active_flows.pop(user_id, None)
            await client.send_message(user_id, "برنامه آزمایشی فعال شد. پس از انتشار سه پست نتیجه را اعلام می‌کنیم.")
            return True

        if state["step"] == "purpose":
            if value == GUIDE:
                await service.clear_draft(user_id)
                active_flows.pop(user_id, None)
                await client.send_message(
                    user_id,
                    "برای ترکیب معرفی محصول، رضایت مشتری و آموزشی، برای هر دسته یک برنامه مستقل بسازید.\n"
                    "اقدام بعدی: ➕ ساخت برنامه جدید",
                )
                return True
            if value not in (RECURRING, DATED):
                await _prompt_purpose(client, user_id)
                return True
            state["program_mode"] = "recurring" if value == RECURRING else "dated"
            state["step"] = "dates" if value == DATED else "cadence"
            await _persist(user_id, state)
            if state["step"] == "dates":
                await client.send_message(user_id, "تاریخ یا بازه کمپین را بفرستید؛ مثال: 1405/03/04 تا 1405/03/10")
            else:
                await _prompt_cadence(client, user_id)
            return True

        if state["step"] == "dates":
            dates = [part.strip() for part in value.split("تا")]
            if len(dates) == 1:
                dates.append(dates[0])
            if len(dates) != 2:
                await client.send_message(user_id, "فرمت تاریخ معتبر نیست؛ مثال: 1405/03/04 تا 1405/03/10")
                return True
            state.update({"start_date": dates[0], "end_date": dates[1], "step": "cadence"})
            await _persist(user_id, state)
            await _prompt_cadence(client, user_id)
            return True

        if state["step"] == "cadence":
            cadence = {INTERVAL: "interval", DAILY_COUNT: "daily_count", EXACT_TIMES: "exact_times"}.get(value)
            if not cadence:
                await _prompt_cadence(client, user_id)
                return True
            state.update({"cadence": cadence, "step": "timing"})
            await _persist(user_id, state)
            examples = {
                "interval": "بازه و فاصله را بفرستید؛ مثال: 08:00 تا 23:59 | 120",
                "daily_count": "بازه و تعداد روزانه را بفرستید؛ مثال: 08:00 تا 23:59 | 3",
                "exact_times": "ساعت‌ها را بفرستید؛ مثال: 09:00 14:00 20:00",
            }
            await client.send_message(user_id, examples[cadence])
            return True

        if state["step"] == "timing":
            config = _parse_timing(state, value)
            PublishingProgramConfig(**config)
            state.update({"config": config, "step": "confirm"})
            await _persist(user_id, state)
            source = state["source"]
            destination = state["destination"]
            await client.send_message(
                user_id,
                f"دسته محتوا: {source.name}\n"
                f"کانال مقصد: {destination.channel_id}\n"
                f"نحوه انتشار: {describe_plan('publishing_program', config)}\n\n"
                f"برای ذخیره «{CONFIRM}» را بفرستید.",
                inline_keypad=_inline_choices(CONFIRM),
            )
            return True

        if state["step"] == "confirm" and value == CONFIRM:
            if state.get("edit_schedule_id"):
                result = await service.update_real_program(
                    user_id, state["edit_schedule_id"], state["source"].id, state["config"]
                )
                completed = "برنامه انتشار به‌روزرسانی شد."
            else:
                result = await service.commit_real_program(user_id, state["destination"], state["source"], state["config"])
                completed = "برنامه انتشار فعال شد."
            active_flows.pop(user_id, None)
            status = (
                "برنامه ذخیره شد و در انتظار محتوا است. با افزودن پست آن را فعال کنید."
                if result["waiting_for_content"]
                else completed
            )
            await client.send_message(user_id, f"✅ {status}")
            return True
    except ValueError as exc:
        await client.send_message(user_id, f"❌ {exc}")
        return True
    except Exception as exc:
        logger.error(f"publishing flow error for {user_id}: {exc}")
        await client.send_message(user_id, "خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        return True
    return True


async def handle_message(client, user_id: str, message: Dict[str, Any]) -> bool:
    """Collect post messages while the wizard owns the conversation."""
    from src.database import pool

    state = active_flows.get(user_id)
    if not state or state.get("step") not in ("tutorial_posts", "real_posts"):
        return False
    text = (message.get("text") or "").strip()
    if state["step"] == "real_posts" and text == SAVE_CATEGORY:
        return await handle_text(client, user_id, text)
    source_id = state["source"].id
    msg_type, content, file_id, caption, raw = _detect_message_type(message)
    if file_id and msg_type != "text":
        file_id = await client.reupload_media(file_id, msg_type)
    await SourceService(pool).add_post(source_id, msg_type, content, file_id, caption, raw)
    state["post_count"] = state.get("post_count", 0) + 1
    if state["step"] == "tutorial_posts":
        count = state["post_count"]
        if count < 3:
            await client.send_message(user_id, f"پست {count} از ۳ ذخیره شد. پست {count + 1} را بفرستید.")
        else:
            state["step"] = "tutorial_interval"
            await _persist(user_id, state)
            await client.send_message(
                user_id,
                "پست ۳ از ۳ ذخیره شد. فاصله انتشار را انتخاب کنید:\n"
                "هر ۱ دقیقه - تست سریع\nهر ۵ دقیقه - پیشنهادی\nهر ۱۰ دقیقه",
                inline_keypad=_inline_choices(
                    "هر ۱ دقیقه - تست سریع", "هر ۵ دقیقه - پیشنهادی", "هر ۱۰ دقیقه"
                ),
            )
    else:
        activated = await PublishingProgramService(pool).activate_waiting_programs(source_id)
        suffix = "\nبرنامه‌های در انتظار محتوا فعال شدند." if activated else ""
        await client.send_message(
            user_id,
            f"{state['post_count']} پست در دسته ذخیره شد.{suffix}\n"
            f"برای ادامه «{SAVE_CATEGORY}» را بفرستید.",
            inline_keypad=_inline_choices(SAVE_CATEGORY),
        )
    return True


async def _prompt_content_choice(client, user_id: str) -> None:
    await client.send_message(
        user_id,
        "چه پست‌هایی قرار است در این کانال منتشر شوند؟\n"
        "پست‌های هم‌موضوع را داخل یک دسته محتوا نگه می‌داریم.\n\n"
        f"{EXISTING_CATEGORY}\n{NEW_CATEGORY}",
        inline_keypad=_inline_choices(EXISTING_CATEGORY, NEW_CATEGORY),
    )


async def _prompt_purpose(client, user_id: str) -> None:
    await client.send_message(
        user_id,
        f"هدف انتشار را انتخاب کنید:\n{RECURRING}\n{DATED}\n{GUIDE}",
        inline_keypad=_inline_choices(RECURRING, DATED, GUIDE),
    )


async def _prompt_cadence(client, user_id: str) -> None:
    await client.send_message(
        user_id,
        f"روش زمان‌بندی را انتخاب کنید:\n{INTERVAL}\n{DAILY_COUNT}\n{EXACT_TIMES}",
        inline_keypad=_inline_choices(INTERVAL, DAILY_COUNT, EXACT_TIMES),
    )


async def _repeat_step_prompt(client, user_id: str, state: Dict[str, Any]) -> None:
    prompts = {
        "channel": lambda: _prompt_channel(client, user_id, state),
        "content_choice": lambda: _prompt_content_choice(client, user_id),
        "purpose": lambda: _prompt_purpose(client, user_id),
        "cadence": lambda: _prompt_cadence(client, user_id),
    }
    if state["step"] in prompts:
        await prompts[state["step"]]()
    else:
        await client.send_message(user_id, "ساخت برنامه ادامه یافت؛ پاسخ مرحله قبلی را دوباره ارسال کنید.")


def _parse_timing(state: Dict[str, Any], value: str) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "program_mode": state["program_mode"],
        "cadence": state["cadence"],
    }
    if state["program_mode"] == "dated":
        config.update({"start_date": state["start_date"], "end_date": state["end_date"]})
    if state["cadence"] == "exact_times":
        config["times"] = [format_hhmm(item) for item in value.split()]
        return config
    match = re.match(r"\s*(\S+)\s+تا\s+(\S+)\s*\|\s*(\d+)\s*$", value)
    if not match:
        raise ValueError("فرمت زمان معتبر نیست.")
    start_time, end_time, number = match.groups()
    config.update({"start_time": format_hhmm(start_time), "end_time": format_hhmm(end_time)})
    config["interval_minutes" if state["cadence"] == "interval" else "daily_count"] = int(number)
    return config
