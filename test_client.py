#!/usr/bin/env python3
"""
Quick test of the KiwiClient against a real Web-888

Usage:
    python3 test_client.py 10.1.1.197
"""

import asyncio
import logging
import sys
from dataclasses import asdict

from kiwi_client import KiwiClient

logging.basicConfig(level=logging.INFO)


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8073

    print(f"\n{'='*60}")
    print(f"Testing KiwiClient against {host}:{port}")
    print(f"{'='*60}\n")

    client = KiwiClient(host, port)

    # Test 1: Get status via HTTP
    print("📡 Fetching status via HTTP...")
    status = await client.get_status()

    print("\n📊 Parsed status:")
    for key, value in asdict(status).items():
        if value:  # Only show non-empty values
            print(f"  {key:20} = {value}")

    print("\n🎯 Key HA sensor values:")
    print(f"  Connected:      {status.connected}")
    print(f"  Users:          {status.users}/{status.users_max}")
    print(f"  Uptime:         {status.uptime}s ({status.uptime/3600:.1f}h)")
    print(f"  GPS Quality:    {status.gps_good}")
    print(f"  GPS Fixes:      {status.fixes} ({status.fixes_min}/min)")
    print(f"  GPS Position:   ({status.gps_lat}, {status.gps_lon})")
    print(f"  Altitude:       {status.asl}m")
    print(f"  Antenna:        {status.antenna}")
    print(f"  Ant Connected:  {status.ant_connected}")
    print(f"  SNR:            {status.snr}")
    print(f"  ADC Overflow:   {status.adc_ov}")
    print(f"  SW Version:     {status.sw_version}")
    print(f"  Device Name:    {status.name}")
    print(f"  Location:       {status.location}")

    # Test 2: WebSocket connection (optional)
    print("\n🔌 Testing WebSocket connection...")
    try:
        connected = await client.connect()
        if connected:
            print("  ✓ WebSocket connected!")

            # Receive a few messages
            print("  Receiving 5 messages...")
            count = 0
            async for msg in client.receive_messages():
                print(f"    {msg.get('type', 'unknown')}: {str(msg)[:80]}...")
                count += 1
                if count >= 5:
                    break

            await client.disconnect()
            print("  ✓ WebSocket disconnected cleanly")
        else:
            print("  ✗ WebSocket connection failed")
    except Exception as e:
        print(f"  ✗ WebSocket error: {e}")

    print(f"\n{'='*60}")
    print("Test complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
