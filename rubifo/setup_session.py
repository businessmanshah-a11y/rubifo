"""
One-time setup script: authenticate your Rubika user account.

Run once:
    python setup_session.py

After entering your phone number and OTP code, a session file
'rubifo_user.session' is saved and the bot can start without
any further interaction.
"""
import asyncio
from rubpy import Client


async def main():
    print("=" * 50)
    print("Rubifo — Rubika User Session Setup")
    print("=" * 50)
    print()
    print("This will log in to your Rubika account.")
    print("You only need to do this once.")
    print()

    client = Client(name="rubifo_user")

    try:
        await client.start()
        me = await client.get_me()
        if me:
            name = getattr(me, "first_name", "") or ""
            phone = getattr(me, "phone", "") or ""
            print()
            print(f"✅ Logged in as: {name}  |  {phone}")
            print()
            print("Session saved to: rubifo_user.session")
            print("You can now start the bot normally.")
        await client.stop()
    except KeyboardInterrupt:
        print("\nAborted.")


if __name__ == "__main__":
    asyncio.run(main())
