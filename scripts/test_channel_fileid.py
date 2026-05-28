"""
Test: Does bot receive channel post updates? Are channel file_ids reusable?
Run: python3 test_channel_fileid.py
"""
import asyncio
import aiohttp
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from src.config import BOT_TOKEN

USER_DM = 'b0HRK4L0eQ801171186fa5bbeb370492'
CHANNEL = '@testrubifo2'
BASE = f'https://botapi.rubika.ir/v3/{BOT_TOKEN}'


async def main():
    async with aiohttp.ClientSession() as s:
        # 1. Get latest updates
        print("=== Step 1: Getting updates ===")
        r = await s.post(f'{BASE}/getUpdates', json={'limit': 30})
        data = await r.json(content_type=None)
        updates = data.get('data', {}).get('updates', [])
        print(f"Total updates: {len(updates)}")

        channel_file_id = None
        channel_msg_id = None

        for u in updates:
            utype = u.get('type', '')
            chat_id = str(u.get('chat_id', ''))
            msg = u.get('new_message') or {}
            file_info = msg.get('file') or {}
            fid = file_info.get('file_id', '')
            mid = msg.get('message_id', '')

            print(f"  type={utype} chat={chat_id[:25]} file={fid[:20] if fid else 'none'}")

            # Check if this update is from the channel with a file
            if fid and (CHANNEL.lower() in chat_id.lower() or 'testrubifo2' in chat_id.lower()):
                channel_file_id = fid
                channel_msg_id = mid
                print(f"  >>> FOUND CHANNEL FILE: file_id={fid[:30]} msg_id={mid}")

        if not channel_file_id:
            print("\n❌ No file from channel found in updates.")
            print("   Either bot doesn't receive channel posts, or no file was posted yet.")
            print("   Try posting a file to @testrubifo2 and run this script again quickly.")
            return

        # 2. Try to sendFile with channel file_id to user DM
        print(f"\n=== Step 2: Trying sendFile to user DM with channel file_id ===")
        print(f"file_id: {channel_file_id[:40]}...")
        r2 = await s.post(f'{BASE}/sendFile', json={
            'chat_id': USER_DM,
            'file_id': channel_file_id,
            'type': 'Image',
        })
        d2 = await r2.json(content_type=None)
        print(f"Result: {d2}")

        if d2.get('status') == 'OK':
            print("\n✅ SUCCESS! Channel file_id works with sendFile!")
            print("   Architecture: post to staging channel → bot reads file_id → sendFile to target")
        else:
            print("\n❌ sendFile with channel file_id also failed.")
            print("   Error:", d2)

        # 3. Also try getFile on the channel file_id
        print(f"\n=== Step 3: Trying getFile on channel file_id ===")
        r3 = await s.post(f'{BASE}/getFile', json={'file_id': channel_file_id})
        d3 = await r3.json(content_type=None)
        dl_url = (d3.get('data') or {}).get('download_url', '')
        print(f"getFile result: {str(d3)[:200]}")

        if dl_url:
            print(f"\n=== Step 4: Trying CDN download from channel file ===")
            async with s.get(dl_url) as resp:
                print(f"CDN download status: {resp.status}")
                if resp.status == 200:
                    content = await resp.read()
                    print(f"✅ DOWNLOAD SUCCESS! {len(content)} bytes")
                else:
                    print(f"❌ CDN still {resp.status}")


asyncio.run(main())
