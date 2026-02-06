#!/usr/bin/env python3
"""
Web-888 API Discovery Script

Run this against a real Web-888 to discover available endpoints and data formats.

Usage:
    python discover_api.py <host> [port]

Example:
    python discover_api.py 10.1.1.197
    python discover_api.py 10.1.1.197 8073
"""

import asyncio
import json
import sys
from urllib.parse import urljoin

import aiohttp


async def probe_endpoint(session: aiohttp.ClientSession, base_url: str, path: str) -> dict:
    """Probe a single endpoint and return results."""
    url = urljoin(base_url, path)
    result = {
        "path": path,
        "url": url,
        "status": None,
        "content_type": None,
        "content": None,
        "error": None,
    }

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            result["status"] = resp.status
            result["content_type"] = resp.headers.get("Content-Type", "")

            if resp.status == 200:
                text = await resp.text()
                result["content"] = text[:2000]  # Limit output
                # Try to parse as JSON
                try:
                    result["json"] = json.loads(text)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        result["error"] = str(e)

    return result


async def discover_web888(host: str, port: int = 8073):
    """Discover available endpoints on a Web-888."""

    base_url = f"http://{host}:{port}"
    print(f"\n{'='*60}")
    print("Web-888 API Discovery")
    print(f"Target: {base_url}")
    print(f"{'='*60}\n")

    # Common KiwiSDR/Web-888 endpoints to probe
    endpoints = [
        "/",
        "/status",
        "/status.json",
        "/stats",
        "/stats.json",
        "/users",
        "/users.json",
        "/config",
        "/config.json",
        "/admin",
        "/admin.json",
        "/gps",
        "/gps.json",
        "/info",
        "/info.json",
        "/api",
        "/api/status",
        "/extensions",
        "/extensions.json",
        "/dx",
        "/dx.json",
        "/kiwi.config",
        "/freq",
        "/freq.json",
    ]

    async with aiohttp.ClientSession() as session:
        print("Probing endpoints...\n")

        for path in endpoints:
            result = await probe_endpoint(session, base_url, path)

            status_str = f"{result['status']}" if result['status'] else "ERROR"
            print(f"  {path:25} -> {status_str:5}", end="")

            if result['status'] == 200:
                ct = result['content_type'][:30] if result['content_type'] else "?"
                print(f"  [{ct}]")

                # Show preview of content
                if result.get('json'):
                    preview = json.dumps(result['json'], indent=2)[:500]
                    print(f"      JSON: {preview}...")
                elif result.get('content'):
                    preview = result['content'][:200].replace('\n', ' ')
                    print(f"      Text: {preview}...")
            elif result['error']:
                print(f"  ({result['error'][:40]})")
            else:
                print()

    print(f"\n{'='*60}")
    print("WebSocket endpoints to test:")
    print(f"  ws://{host}:{port}/12345678/SND   (audio stream)")
    print(f"  ws://{host}:{port}/12345678/W/F   (waterfall)")
    print(f"{'='*60}\n")


async def test_websocket(host: str, port: int = 8073):
    """Test WebSocket connection."""
    import websockets

    url = f"ws://{host}:{port}/12345678/SND"
    print(f"\nTesting WebSocket: {url}")

    try:
        async with websockets.connect(url, close_timeout=5) as ws:
            print("  Connected!")

            # Send auth
            await ws.send("SET auth t=kiwi p=#")
            print("  Sent: SET auth t=kiwi p=#")

            # Receive a few messages
            print("  Receiving messages (5 seconds)...")
            try:
                for _i in range(10):
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    if isinstance(msg, bytes):
                        print(f"    Binary: {len(msg)} bytes, header: {msg[:10].hex()}")
                    else:
                        print(f"    Text: {msg[:100]}...")
            except asyncio.TimeoutError:
                print("    (timeout waiting for messages)")

            print("  WebSocket test complete!")

    except Exception as e:
        print(f"  WebSocket error: {e}")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8073

    await discover_web888(host, port)

    # Ask about websocket test
    try:
        import websockets  # noqa: F401
        await test_websocket(host, port)
    except ImportError:
        print("Note: Install 'websockets' package for WebSocket testing")


if __name__ == "__main__":
    asyncio.run(main())
