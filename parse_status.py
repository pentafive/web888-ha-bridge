#!/usr/bin/env python3
"""
Parse the /status endpoint from Web-888

Usage:
    python3 parse_status.py 10.1.1.197
"""

import asyncio
import sys

import aiohttp


async def get_status(host: str, port: int = 8073):
    url = f"http://{host}:{port}/status"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            text = await resp.text()

    print(f"Raw status from {host}:\n{'='*60}")
    print(text)
    print('='*60)

    print("\nParsed key=value pairs:")
    print('-'*60)

    # Parse each LINE as key=value (not space-separated!)
    parsed = {}
    for line in text.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            parsed[key] = value
            print(f"  {key:20} = {value}")

    print('-'*60)
    print(f"\nTotal keys: {len(parsed)}")

    # Key metrics for Home Assistant
    print("\n🎯 Key metrics for HA sensors:")
    metrics = ['users', 'users_max', 'gps', 'fixes', 'fixes_min', 'lat', 'lon',
               'adc_clk_nom', 'freq', 'snr', 'rssi']
    for m in metrics:
        if m in parsed:
            print(f"  ✓ {m} = {parsed[m]}")
        else:
            print(f"  ✗ {m} (not found)")

    return parsed


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8073

    await get_status(host, port)


if __name__ == "__main__":
    asyncio.run(main())
