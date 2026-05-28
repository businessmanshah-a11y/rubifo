"""
Test: After enabling 'receive all channel messages', does bot now get channel post updates?
And can it sendFile with the channel file_id to another chat?
Run: python3 test_channel_update.py
"""
import asyncio
import aiohttp
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from src.config import BOT_TOKEN

USER_DM = 'b0HRK4L0eQ801171186fa5bbeb370492'
BASE = f'https://botapi.rubika.ir/v3/{BOT_TOKEN}'


async def main():
    async with aiohttp.ClientSession() as s:

        print("=== Step 1: Getting ALL updates (no offset) ===")
        r = await s.post(f'{BASE}/getUpdates', json={'limit': 50})
        data = await r.json(content_type=None)
        updates = data.get('data', {}).get('updates', [])
        print(f"Total updates: {len(updates)}")

        channel_entries = []
        for u in updates:
            utype = u.get('type', '')
            chat_id = str(u.get('chat_id', ''))
            msg = u.get('new_message') or {}
            file_info = msg.get('file') or {}
            fid = file_info.get('file_id', '')
            mid = str(msg.get('message_id', ''))
            text = msg.get('text', '')

            # Show all non-DM updates
            if 'b0HRK4L0' not in chat_id:
                print(f"  >>> NON-DM: type={utype} chat={chat_id[:30]} file={fid[:20] if fid else 'none'} text={text[:20]}")
                if fid:
                    channel_entries.append({'file_id': fid, 'msg_id': mid, 'chat_id': chat_id, 'type': utype})
            else:
                if fid:
                    print(f"  DM with file: type={utype} file={fid[:20]}")

        if not channel_entries:
            print("\n❌ No channel updates found yet.")
            print("   POST A FILE TO @testrubifo2 NOW and run this script again!")
            return

        # Try sendFile with channel file_id
        entry = channel_entries[-1]
        print(f"\n=== Step 2: sendFile to user DM with channel file_id ===")
        print(f"  file_id: {entry['file_id'][:40]}")

        r2 = await s.post(f'{BASE}/sendFile', json={
            'chat_id': USER_DM,
            'file_id': entry['file_id'],
            'type': 'Image',
        })
        d2 = await r2.json(content_type=None)
        print(f"  sendFile result: {d2}")

        if d2.get('status') == 'OK':
            print("\n✅✅✅ SUCCESS! Channel file_id works with sendFile — NO attribution!")
            print("   NEW ARCHITECTURE: source channel → bot reads file_id → sendFile to target")
        else:
            print(f"\n❌ sendFile failed: {d2}")

            # Try getFile + download
            print(f"\n=== Step 3: Try download via getFile ===")
            r3 = await s.post(f'{BASE}/getFile', json={'file_id': entry['file_id']})
            d3 = await r3.json(content_type=None)
            dl_url = (d3.get('data') or {}).get('download_url', '')
            print(f"  getFile: {str(d3)[:150]}")
            if dl_url:
                async with s.get(dl_url) as resp:
                    print(f"  CDN download: {resp.status}")
                    if resp.status == 200:
                        body = await resp.read()
                        print(f"  ✅ Downloaded {len(body)} bytes!")


asyncio.run(main())
