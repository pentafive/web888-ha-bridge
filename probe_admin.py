#!/usr/bin/env python3
"""
Web-888 Admin Endpoint Discovery

Probes endpoints with and without authentication to discover what's available.

Usage:
    python3 probe_admin.py <host> [password]

Example:
    python3 probe_admin.py 10.1.1.197
    python3 probe_admin.py 10.1.1.197 mysecretpassword
"""

import asyncio
import sys
from urllib.parse import urljoin

import aiohttp


async def probe_endpoint(session: aiohttp.ClientSession, url: str, auth_cookie: str = None) -> dict:
    """Probe a single endpoint."""
    headers = {}
    cookies = {}

    if auth_cookie:
        cookies["kiwi"] = auth_cookie

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5),
                               headers=headers, cookies=cookies) as resp:
            return {
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type", ""),
                "content": await resp.text() if resp.status == 200 else None,
            }
    except Exception as e:
        return {"status": None, "error": str(e)}


async def attempt_login(session: aiohttp.ClientSession, base_url: str, password: str) -> str | None:
    """Attempt to authenticate and get session cookie."""
    # KiwiSDR uses various auth mechanisms, try common ones

    auth_endpoints = [
        f"{base_url}/admin",
        f"{base_url}/login",
        f"{base_url}/auth",
    ]

    # Try POST with password
    for endpoint in auth_endpoints:
        try:
            async with session.post(
                endpoint,
                data={"password": password, "pwd": password, "p": password},
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False
            ) as resp:
                if resp.status in (200, 302):
                    # Check for session cookie
                    if "kiwi" in resp.cookies:
                        return resp.cookies["kiwi"].value
                    # Check for set-cookie header
                    for cookie in resp.headers.getall("Set-Cookie", []):
                        if "kiwi=" in cookie:
                            return cookie.split("kiwi=")[1].split(";")[0]
        except:
            pass

    # Try URL parameter auth (common in embedded devices)
    try:
        async with session.get(
            f"{base_url}/admin?pwd={password}",
            timeout=aiohttp.ClientTimeout(total=5),
            allow_redirects=False
        ) as resp:
            if "kiwi" in resp.cookies:
                return resp.cookies["kiwi"].value
    except:
        pass

    return None


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    host = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    port = 8073
    base_url = f"http://{host}:{port}"

    print(f"\n{'='*60}")
    print("Web-888 Admin Endpoint Discovery")
    print(f"Target: {base_url}")
    print(f"Password: {'provided' if password else 'not provided'}")
    print(f"{'='*60}\n")

    # Endpoints to probe
    admin_endpoints = [
        "/admin",
        "/admin.html",
        "/admin/",
        "/admin/status",
        "/admin/config",
        "/admin/network",
        "/admin/update",
        "/admin/log",
        "/admin/console",
        "/admin/extensions",
        "/admin/dx",
        "/admin/security",
        "/admin/backup",
        "/admin/restart",
        "/admin/password",
        "/admin/users",
        "/mfg",
        "/mfg.html",
        "/kiwisdr.config",
        "/kiwi/config",
        "/config/admin",
        "/settings",
        "/system",
        "/debug",
        "/log",
        "/console",
        "/reboot",
        "/update",
    ]

    async with aiohttp.ClientSession() as session:
        # First, try without auth
        print("🔓 Probing without authentication:\n")
        for path in admin_endpoints[:10]:  # First 10 for quick test
            url = urljoin(base_url, path)
            result = await probe_endpoint(session, url)
            status = result.get("status", "ERR")
            print(f"  {path:25} -> {status}")

        # If password provided, try auth
        if password:
            print("\n🔐 Attempting authentication...")
            auth_cookie = await attempt_login(session, base_url, password)

            if auth_cookie:
                print(f"  ✓ Got auth cookie: {auth_cookie[:20]}...")
            else:
                print("  ✗ Auth cookie not obtained (may use different mechanism)")
                # Try passing password as URL param
                print("  Trying password as URL parameter...")

            print("\n🔒 Probing WITH authentication:\n")
            for path in admin_endpoints:
                # Try with cookie if we have it
                url = urljoin(base_url, path)
                result = await probe_endpoint(session, url, auth_cookie)
                status1 = result.get("status", "ERR")

                # Also try with URL param
                url_with_pwd = f"{url}?pwd={password}"
                result2 = await probe_endpoint(session, url_with_pwd)
                status2 = result2.get("status", "ERR")

                indicator = ""
                if status1 == 200 or status2 == 200:
                    indicator = " ✓"
                print(f"  {path:25} -> cookie:{status1} url:{status2}{indicator}")

                # Show content preview for successful endpoints
                if result.get("content") and status1 == 200:
                    preview = result["content"][:100].replace("\n", " ")
                    print(f"      Preview: {preview}...")
                elif result2.get("content") and status2 == 200:
                    preview = result2["content"][:100].replace("\n", " ")
                    print(f"      Preview: {preview}...")

    # Security observations
    print(f"\n{'='*60}")
    print("🛡️ Security Notes for HA Bridge:")
    print("-"*60)
    print("""
1. The /status endpoint is PUBLIC (no auth required)
   - This is intentional for SDR aggregator sites
   - Good for HA monitoring without credentials

2. WebSocket connections may require password for some features
   - Basic audio streaming often works without auth
   - Admin functions require authentication

3. For the HA bridge, consider:
   - Store admin password in .env (not in code)
   - Use MQTT user/pass for HA communication
   - The bridge only needs read access (no admin functions)

4. Device security recommendations:
   - Use a strong admin password
   - Consider firewall rules (VLAN isolation)
   - The Web-888 exposes web interface on port 8073
""")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
