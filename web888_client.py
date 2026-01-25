"""
Web-888/KiwiSDR Client Library

Supports two modes:
1. Simple HTTP mode - polls /status endpoint (no auth required)
2. Full WebSocket mode - connects to admin interface for rich data (auth required)

Usage:
    # Simple mode (no auth)
    client = Web888Client("192.168.1.100", mode="http")
    await client.connect()
    status = client.status

    # Full mode (with auth)
    client = Web888Client("192.168.1.100", mode="websocket", password="admin")
    await client.connect()
    status = client.status  # Includes CPU temp, channels, GPS satellites
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import unquote

import aiohttp

logger = logging.getLogger(__name__)


class ClientMode(Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"


@dataclass
class ChannelInfo:
    """Information about a single RX channel."""
    index: int = 0
    name: str = ""
    frequency_hz: int = 0
    mode: str = ""
    extension: str = ""
    decoded_count: int = 0
    client_ip: str = ""
    session_time: str = ""

    @property
    def frequency_mhz(self) -> float:
        return self.frequency_hz / 1_000_000

    @property
    def frequency_khz(self) -> float:
        return self.frequency_hz / 1_000


@dataclass
class GPSSatellite:
    """GPS satellite tracking info."""
    channel: int = 0
    system: str = ""  # N=NavStar, G=GLONASS, B=BeiDou
    prn: int = 0
    snr: int = 0
    rssi: int = 0
    azimuth: int = 0
    elevation: int = 0
    in_solution: bool = False


@dataclass
class GPSStatus:
    """GPS receiver status."""
    acquiring: bool = False
    tracking: int = 0
    good: int = 0
    fixes: int = 0
    fixes_per_min: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: int = 0
    grid_square: str = ""
    adc_clock_mhz: float = 0.0
    satellites: list = field(default_factory=list)


@dataclass
class SystemStats:
    """System hardware statistics (WebSocket mode only)."""
    cpu_temp_c: float = 0.0
    cpu_freq_mhz: float = 0.0
    cpu_user_pct: list = field(default_factory=list)
    cpu_sys_pct: list = field(default_factory=list)
    cpu_idle_pct: list = field(default_factory=list)
    audio_kbps: float = 0.0
    waterfall_kbps: float = 0.0
    http_kbps: float = 0.0
    total_kbps: float = 0.0
    dropped: int = 0
    underruns: int = 0


@dataclass
class Web888Status:
    """Complete status from Web-888 SDR."""
    # Connection info
    connected: bool = False
    mode: str = "http"
    last_update: float = 0.0

    # Basic info (available in both modes)
    name: str = ""
    location: str = ""
    sw_version: str = ""
    antenna: str = ""
    bands: str = ""
    uptime_seconds: int = 0
    users: int = 0
    users_max: int = 0
    status: str = ""  # private/public
    offline: bool = False
    op_email: str = ""

    # Antenna/ADC
    ant_connected: bool = False
    adc_overflow: int = 0
    snr: str = ""

    # GPS (basic in HTTP, detailed in WebSocket)
    gps: GPSStatus = field(default_factory=GPSStatus)

    # WebSocket-only data
    system: SystemStats = field(default_factory=SystemStats)
    channels: list = field(default_factory=list)  # List[ChannelInfo]

    @property
    def uptime_formatted(self) -> str:
        """Format uptime as HH:MM:SS."""
        hours = self.uptime_seconds // 3600
        minutes = (self.uptime_seconds % 3600) // 60
        seconds = self.uptime_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"


class Web888Client:
    """
    Async client for Web-888/KiwiSDR receivers.

    Supports two modes:
    - HTTP: Simple polling of /status endpoint (no auth)
    - WebSocket: Full admin connection for rich data (auth required)
    """

    def __init__(
        self,
        host: str,
        port: int = 8073,
        mode: str = "http",
        password: str = "",
        poll_interval: int = 30,
        on_update: Callable[["Web888Status"], None] | None = None,
    ):
        self.host = host
        self.port = port
        self.mode = ClientMode(mode)
        self.password = password
        self.poll_interval = poll_interval
        self.on_update = on_update

        self.status = Web888Status(mode=mode)
        self._running = False
        self._poll_task: asyncio.Task | None = None
        self._ws = None
        self._ws_task: asyncio.Task | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def ws_url(self) -> str:
        timestamp = int(time.time() * 1000000)
        return f"ws://{self.host}:{self.port}/kiwi/{timestamp}/admin"

    async def connect(self) -> bool:
        """Connect to the Web-888."""
        try:
            if self.mode == ClientMode.HTTP:
                # Just fetch status once to verify connection
                success = await self._fetch_http_status()
                if success:
                    self._running = True
                    self._poll_task = asyncio.create_task(self._http_poll_loop())
                return success
            else:
                # WebSocket mode
                return await self._connect_websocket()
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the Web-888."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        self.status.connected = False
        logger.info(f"Disconnected from Web-888 at {self.host}")

    async def update(self) -> Web888Status:
        """Force an immediate status update."""
        if self.mode == ClientMode.HTTP:
            await self._fetch_http_status()
        # WebSocket updates continuously
        return self.status

    # ========== HTTP Mode ==========

    async def _http_poll_loop(self):
        """Background loop to poll status."""
        while self._running:
            try:
                await asyncio.sleep(self.poll_interval)
                await self._fetch_http_status()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Poll error: {e}")

    async def _fetch_http_status(self) -> bool:
        """Fetch status from HTTP endpoint."""
        url = f"{self.base_url}/status"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        self._parse_http_status(text)
                        self.status.connected = True
                        self.status.last_update = time.time()

                        if self.on_update:
                            self.on_update(self.status)

                        return True
                    else:
                        logger.warning(f"HTTP status failed: {resp.status}")
                        self.status.connected = False
                        return False
        except Exception as e:
            logger.error(f"HTTP fetch failed: {e}")
            self.status.connected = False
            return False

    def _parse_http_status(self, text: str):
        """Parse key=value status response."""
        for line in text.strip().split("\n"):
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            try:
                if key == "name":
                    self.status.name = value
                elif key == "loc":
                    self.status.location = value
                elif key == "sw_version":
                    self.status.sw_version = value
                elif key == "antenna":
                    self.status.antenna = value
                elif key == "bands":
                    self.status.bands = value
                elif key == "uptime":
                    self.status.uptime_seconds = int(value)
                elif key == "users":
                    self.status.users = int(value)
                elif key == "users_max":
                    self.status.users_max = int(value)
                elif key == "status":
                    self.status.status = value
                elif key == "offline":
                    self.status.offline = value == "yes"
                elif key == "ant_connected":
                    self.status.ant_connected = value == "1"
                elif key == "adc_ov":
                    self.status.adc_overflow = int(value)
                elif key == "snr":
                    self.status.snr = value
                elif key == "gps":
                    # Format: (lat, lon)
                    coords = value.strip("()").split(",")
                    if len(coords) >= 2:
                        self.status.gps.latitude = float(coords[0].strip())
                        self.status.gps.longitude = float(coords[1].strip())
                elif key == "gps_good":
                    self.status.gps.good = int(value)
                elif key == "fixes":
                    self.status.gps.fixes = int(value)
                elif key == "fixes_min":
                    self.status.gps.fixes_per_min = int(value)
                elif key == "asl":
                    self.status.gps.altitude_m = int(value)
                elif key == "op_email":
                    self.status.op_email = value
            except (ValueError, IndexError) as e:
                logger.debug(f"Parse error for {key}={value}: {e}")

    # ========== WebSocket Mode ==========

    async def _connect_websocket(self) -> bool:
        """Connect to admin WebSocket."""
        try:
            import websockets

            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=None,
                close_timeout=10,
            )

            # Send auth
            if self.password:
                await self._ws.send(f"SET auth t=admin p={self.password}")

            # Drain initial config messages, check first badp response
            auth_checked = False
            for _ in range(20):
                try:
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=0.3)
                    text = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else msg

                    # Only check the FIRST badp message (auth response)
                    if not auth_checked and "MSG badp=" in text:
                        if "badp=0" in text:
                            logger.debug("Authentication successful")
                            auth_checked = True
                        else:
                            logger.error(f"Authentication failed: {text}")
                            return False

                    # Stop draining after config is loaded
                    if "cfg_loaded" in text:
                        break
                except asyncio.TimeoutError:
                    break

            # Start receive loop and poll loop
            self._running = True
            self._ws_task = asyncio.create_task(self._ws_receive_loop())
            self._poll_task = asyncio.create_task(self._ws_poll_loop())

            self.status.connected = True
            logger.info(f"WebSocket connected to {self.host}")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.status.connected = False
            return False

    async def _ws_poll_loop(self):
        """Periodically request status updates via WebSocket."""
        while self._running and self._ws:
            try:
                # Request stats and users
                await self._ws.send("SET STATS_UPD ch=0")
                await asyncio.sleep(0.5)
                await self._ws.send("SET GET_USERS")
                await asyncio.sleep(0.5)
                await self._ws.send("SET gps_update")

                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"WS poll error: {e}")
                self.status.connected = False
                break  # Exit loop on error, let reconnect handle it

    async def _ws_receive_loop(self):
        """Process incoming WebSocket messages."""
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    self._parse_ws_message(message)
                    self.status.last_update = time.time()

                    if self.on_update:
                        self.on_update(self.status)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            self.status.connected = False

    def _parse_ws_message(self, data: bytes):
        """Parse binary WebSocket message."""
        try:
            text = data.decode("utf-8", errors="ignore")

            if not text.startswith("MSG "):
                return

            content = text[4:]
            eq_idx = content.find("=")
            if eq_idx < 0:
                return

            msg_type = content[:eq_idx]
            msg_value = content[eq_idx + 1:]

            if msg_type == "user_cb":
                self._parse_user_cb(msg_value)
            elif msg_type == "stats_cb":
                self._parse_stats_cb(msg_value)
            elif msg_type == "gps_update_cb":
                self._parse_gps_update_cb(msg_value)
            elif msg_type == "gps_POS_data_cb":
                self._parse_gps_pos_cb(msg_value)

        except Exception as e:
            logger.debug(f"Message parse error: {e}")

    def _parse_user_cb(self, value: str):
        """Parse channel/user data."""
        try:
            data = json.loads(value)
            channels = []

            for ch in data:
                # Decode URL-encoded status (e.g., "410%20decoded" -> "410 decoded")
                status_str = unquote(ch.get("g", ""))
                decoded_count = 0
                if "decoded" in status_str:
                    try:
                        decoded_count = int(status_str.split()[0])
                    except (ValueError, IndexError):
                        pass

                channel = ChannelInfo(
                    index=ch.get("i", 0),
                    name=ch.get("n", ""),
                    frequency_hz=ch.get("f", 0),
                    mode=ch.get("m", ""),
                    extension=ch.get("e", ""),
                    decoded_count=decoded_count,
                    client_ip=ch.get("a", ""),
                    session_time=ch.get("t", ""),
                )
                channels.append(channel)

            self.status.channels = channels
            self.status.users = len([c for c in channels if c.client_ip])

        except json.JSONDecodeError as e:
            logger.debug(f"user_cb JSON error: {e}")

    def _parse_stats_cb(self, value: str):
        """Parse system statistics."""
        try:
            data = json.loads(value)

            self.status.uptime_seconds = data.get("ct", 0)
            self.status.system.cpu_temp_c = data.get("cc", 0)
            self.status.system.cpu_freq_mhz = data.get("cf", 0)
            self.status.system.cpu_user_pct = data.get("cu", [])
            self.status.system.cpu_sys_pct = data.get("cs", [])
            self.status.system.cpu_idle_pct = data.get("ci", [])
            self.status.system.audio_kbps = data.get("ac", 0)
            self.status.system.waterfall_kbps = data.get("wc", 0)
            self.status.system.http_kbps = data.get("ah", 0)
            self.status.system.dropped = data.get("ad", 0)
            self.status.system.underruns = data.get("au", 0)

            # GPS from stats
            self.status.gps.acquiring = data.get("ga", 0) == 1
            self.status.gps.tracking = data.get("gt", 0)
            self.status.gps.good = data.get("gg", 0)
            self.status.gps.fixes = data.get("gf", 0)
            self.status.gps.adc_clock_mhz = data.get("gc", 0)
            self.status.gps.grid_square = data.get("gr", "")

        except json.JSONDecodeError as e:
            logger.debug(f"stats_cb JSON error: {e}")

    def _parse_gps_update_cb(self, value: str):
        """Parse per-satellite GPS data."""
        try:
            # URL decode first
            decoded = unquote(value)
            data = json.loads(decoded)

            satellites = []
            for sat in data.get("ch", []):
                satellite = GPSSatellite(
                    channel=sat.get("ch", 0),
                    system=sat.get("prn_s", ""),
                    prn=sat.get("prn", 0),
                    snr=sat.get("snr", 0),
                    rssi=sat.get("rssi", 0),
                    azimuth=sat.get("az", 0),
                    elevation=sat.get("el", 0),
                    in_solution=sat.get("soln", 0) == 1,
                )
                satellites.append(satellite)

            self.status.gps.satellites = satellites

        except json.JSONDecodeError as e:
            logger.debug(f"gps_update_cb JSON error: {e}")

    def _parse_gps_pos_cb(self, value: str):
        """Parse GPS position data."""
        try:
            decoded = unquote(value)
            data = json.loads(decoded)

            self.status.gps.latitude = data.get("ref_lat", 0.0)
            self.status.gps.longitude = data.get("ref_lon", 0.0)

        except json.JSONDecodeError as e:
            logger.debug(f"gps_POS_data_cb JSON error: {e}")


# ========== CLI Testing ==========

async def test_http_mode(host: str):
    """Test HTTP mode."""
    print(f"\n=== Testing HTTP Mode on {host} ===\n")

    client = Web888Client(host, mode="http")

    if await client.connect():
        print(f"Connected: {client.status.connected}")
        print(f"Name: {client.status.name}")
        print(f"Version: {client.status.sw_version}")
        print(f"Location: {client.status.location}")
        print(f"Uptime: {client.status.uptime_formatted}")
        print(f"Users: {client.status.users}/{client.status.users_max}")
        print(f"GPS Fixes: {client.status.gps.fixes}")
        print(f"Antenna: {client.status.ant_connected}")

        await client.disconnect()
    else:
        print("Failed to connect")


async def test_websocket_mode(host: str, password: str):
    """Test WebSocket mode."""
    print(f"\n=== Testing WebSocket Mode on {host} ===\n")

    def on_update(status: Web888Status):
        print(f"[Update] CPU: {status.system.cpu_temp_c}°C, "
              f"Channels: {len(status.channels)}, "
              f"GPS: {status.gps.grid_square}")

    client = Web888Client(host, mode="websocket", password=password, on_update=on_update)

    if await client.connect():
        print("Connected, receiving updates for 10 seconds...")
        await asyncio.sleep(10)

        print("\n=== Final Status ===")
        print(f"CPU Temp: {client.status.system.cpu_temp_c}°C")
        print(f"CPU Freq: {client.status.system.cpu_freq_mhz} MHz")
        print(f"Grid: {client.status.gps.grid_square}")
        print(f"GPS Lat/Lon: {client.status.gps.latitude}, {client.status.gps.longitude}")
        print(f"GPS Satellites: {len(client.status.gps.satellites)}")

        print("\n=== Channels ===")
        for ch in client.status.channels:
            print(f"  RX{ch.index}: {ch.name} @ {ch.frequency_khz:.2f} kHz "
                  f"({ch.extension}) - {ch.decoded_count} decoded")

        await client.disconnect()
    else:
        print("Failed to connect")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Web-888 SDR Client")
    parser.add_argument("host", help="Web-888 host IP")
    parser.add_argument("--mode", choices=["http", "websocket"], default="http")
    parser.add_argument("--password", default="", help="Admin password (for websocket mode)")

    args = parser.parse_args()

    if args.mode == "http":
        asyncio.run(test_http_mode(args.host))
    else:
        asyncio.run(test_websocket_mode(args.host, args.password))
