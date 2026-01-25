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

# v1.2.1: Timeout constants (seconds)
HTTP_TIMEOUT = 10
WS_PING_INTERVAL = 20
WS_PING_TIMEOUT = 10
WS_CLOSE_TIMEOUT = 10
CONFIG_DRAIN_TIMEOUT = 5.0


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
    session_time: str = ""  # Format: "HHH:MM:SS" e.g. "518:00:56"
    preemptible: bool = False  # v1.2.1: Can be preempted by users

    @property
    def session_seconds(self) -> int:
        """Convert session_time (HHH:MM:SS) to total seconds."""
        if not self.session_time:
            return 0
        try:
            parts = self.session_time.split(":")
            if len(parts) == 3:
                hours, mins, secs = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + mins * 60 + secs
        except (ValueError, IndexError):
            pass
        return 0

    @property
    def frequency_mhz(self) -> float:
        return self.frequency_hz / 1_000_000

    @property
    def frequency_khz(self) -> float:
        return self.frequency_hz / 1_000

    @property
    def is_extension(self) -> bool:
        """True if this is an extension (FT8/WSPR/etc) not a real user."""
        return bool(self.extension) or self.client_ip == "127.0.0.1"

    @property
    def channel_type(self) -> str:
        """Return channel type: 'ft8', 'wspr', 'user', or 'idle'."""
        if not self.client_ip:
            return "idle"
        ext_lower = self.extension.lower()
        if ext_lower in ("ft8", "ft4"):
            return "ft8"
        elif ext_lower == "wspr":
            return "wspr"
        elif self.extension:
            return self.extension.lower()
        elif self.client_ip == "127.0.0.1":
            return "local"
        else:
            return "user"


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
    fixes_per_hour: int = 0  # v1.1.0: GPS fixes per hour from HTTP /status
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
    # v1.2.1: Additional diagnostic counters (from stats "0 sequence, 0 realtime")
    sequence_errors: int = 0
    realtime_errors: int = 0


@dataclass
class ReporterConfig:
    """FT8/WSPR reporter configuration (from WebSocket cfg).

    Web-888 has separate config sections for WSPR and FT8:
    - WSPR: callsign, grid (used for wsprnet.org)
    - FT8: callsign, grid, SNR_adj, dT_adj (used for PSKReporter)

    When FT8 callsign/grid are empty, WSPR values are used as fallback.
    """

    # WSPR reporter identity (for wsprnet.org)
    wspr_callsign: str = ""
    wspr_grid: str = ""

    # FT8 reporter identity (for PSKReporter) - often empty, uses WSPR as fallback
    ft8_callsign: str = ""
    ft8_grid: str = ""

    # FT8-specific corrections (applied before reporting to PSKReporter)
    snr_correction: int = 0  # SNR_adj
    dt_correction: int = 0   # dT_adj

    # Autorun slots: band codes for channels 0-11 (0=disabled)
    # Band codes: 2=160m, 3=80m, 4=60m, 5=40m, 6=30m, 7=20m, 8=17m,
    #            9=15m, 10=12m, 11=10m, 12=6m, 13=2m, 14=630m, 15=2200m
    autorun: list = field(default_factory=list)  # WSPR autorun
    ft8_autorun: list = field(default_factory=list)  # FT8 autorun

    @property
    def callsign(self) -> str:
        """Effective reporter callsign (FT8 if set, else WSPR)."""
        return self.ft8_callsign or self.wspr_callsign

    @property
    def grid(self) -> str:
        """Effective reporter grid (FT8 if set, else WSPR)."""
        return self.ft8_grid or self.wspr_grid


@dataclass
class DeviceConfig:
    """Device configuration from WebSocket load_cfg and load_adm messages.

    This captures the full device config for monitoring and future control.
    """

    # Calibration (from load_cfg)
    s_meter_cal: int = 0  # S-meter calibration offset (dB)
    waterfall_cal: int = 0  # Waterfall calibration offset (dB)
    dc_offset_i: float = 0.0  # DC offset I
    dc_offset_q: float = 0.0  # DC offset Q
    clk_adj: int = 0  # Clock adjustment
    adc_clk_corr: int = 0  # ADC clock correction (ADC_clk2_corr)
    overload_mute: int = 0  # Overload mute threshold (dB)

    # Feature flags (from load_cfg)
    drm_enabled: bool = False  # DRM decoder enabled
    wspr_enabled: bool = False  # WSPR extension enabled
    wspr_spot_log: bool = False  # WSPR spot logging to file
    wspr_syslog: bool = False  # WSPR syslog reporting
    wspr_gps_update_grid: bool = False  # Auto-update grid from GPS
    spectral_inversion: bool = False  # Spectral inversion mode
    ext_adc_clk: bool = False  # External ADC clock in use
    no_waterfall: bool = False  # Waterfall disabled

    # Session/access config (from load_cfg)
    inactivity_timeout_mins: int = 0  # User session timeout
    ip_limit_mins: int = 0  # IP rate limiting
    chan_no_pwd: int = 0  # Password-free channels
    n_camp: int = 0  # Camping connections allowed
    ext_api_nchans: int = 0  # API-accessible channels
    tdoa_nchans: int = 0  # TDoA channels

    # Noise reduction settings (from load_cfg)
    nb_algo: int = 0  # Noise blanker algorithm
    nb_thresh: int = 0  # Noise blanker threshold
    nb_gate: int = 0  # Noise blanker gate
    nr_algo: int = 0  # Noise reduction algorithm

    # Device info (from load_cfg)
    rx_name: str = ""  # Device name
    rx_device: str = ""  # Device type (WEB-888)
    rx_location: str = ""  # Location string
    rx_antenna: str = ""  # Antenna description
    rx_asl: int = 0  # Altitude ASL (meters)
    rx_gps: str = ""  # Configured GPS coords
    owner_info: str = ""  # Owner email
    admin_email: str = ""  # Admin contact
    tdoa_server: str = ""  # TDoA server URL

    # Admin config (from load_adm)
    enable_gps: bool = True  # GPS enabled
    gps_corr: bool = True  # GPS frequency correction
    airband: bool = False  # Airband mode
    narrowband: bool = False  # Narrowband mode
    wf_share: bool = False  # Waterfall sharing
    server_enabled: bool = True  # Server accepting connections
    use_ssl: bool = False  # SSL enabled
    sdr_hu_register: bool = False  # Listed on sdr.hu
    kiwisdr_com_register: bool = False  # Listed on kiwisdr.com
    ip_blacklist_auto: bool = False  # Auto-updating blacklist
    ip_blacklist_mtime: int = 0  # Last blacklist update timestamp

    # Network config (from load_adm)
    configured_ip: str = ""  # Static IP if set
    use_static_ip: bool = False  # Static IP mode
    port: int = 8073  # Service port
    netmask: str = ""  # Network mask
    gateway: str = ""  # Default gateway

    # v1.2.1: Device identity (from config_cb message)
    mac_address: str = ""  # Ethernet MAC address
    serial_number: str = ""  # Device serial number
    dna: str = ""  # Hardware DNA/ID


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

    # v1.1.0: Additional HTTP /status fields
    sdr_hw: str = ""  # Hardware description (e.g., "KiwiSDR v2024.1130")
    freq_offset: float = 0.0  # Frequency calibration offset in Hz

    # GPS (basic in HTTP, detailed in WebSocket)
    gps: GPSStatus = field(default_factory=GPSStatus)

    # WebSocket-only data
    system: SystemStats = field(default_factory=SystemStats)
    channels: list = field(default_factory=list)  # List[ChannelInfo]
    reporter: ReporterConfig = field(default_factory=ReporterConfig)  # FT8/WSPR config
    config: DeviceConfig = field(default_factory=DeviceConfig)  # Full device config

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
        # v1.2.1: Reusable HTTP session for connection pooling
        self._http_session: aiohttp.ClientSession | None = None

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

        # v1.2.1: Close HTTP session to prevent resource leaks
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

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

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create reusable HTTP session."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            )
        return self._http_session

    async def fetch_http_status(self) -> bool:
        """Fetch status from HTTP endpoint (public method)."""
        url = f"{self.base_url}/status"

        try:
            session = await self._get_http_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    self._parse_http_status(text)
                    self.status.connected = True
                    self.status.last_update = time.time()

                    if self.on_update:
                        try:
                            self.on_update(self.status)
                        except Exception as cb_err:
                            logger.error(f"on_update callback error: {cb_err}")

                    return True
                else:
                    logger.warning(f"HTTP status failed: {resp.status}")
                    self.status.connected = False
                    return False
        except Exception as e:
            logger.error(f"HTTP fetch failed: {e}")
            self.status.connected = False
            return False

    # v1.2.1: Keep old name as alias for backward compatibility
    _fetch_http_status = fetch_http_status

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
                # v1.1.0: Additional HTTP /status fields
                elif key == "sdr_hw":
                    self.status.sdr_hw = value
                elif key == "freq_offset":
                    self.status.freq_offset = float(value)
                elif key == "fixes_hour":
                    self.status.gps.fixes_per_hour = int(value)
            except (ValueError, IndexError) as e:
                logger.debug(f"Parse error for {key}={value}: {e}")

    # ========== WebSocket Mode ==========

    async def _connect_websocket(self) -> bool:
        """Connect to admin WebSocket."""
        try:
            import websockets

            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            # v1.2.1: Enable keep-alive pings to detect dead connections
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=WS_PING_INTERVAL,
                ping_timeout=WS_PING_TIMEOUT,
                close_timeout=WS_CLOSE_TIMEOUT,
            )

            # Send auth (note: KiwiSDR protocol sends password in plaintext - unavoidable)
            if self.password:
                logger.debug("Sending WebSocket authentication")
                await self._ws.send(f"SET auth t=admin p={self.password}")

            # Drain initial config messages, check first badp response
            # v1.2.1: Add overall timeout to prevent slow connections from hanging
            auth_checked = False
            auth_required = bool(self.password)
            drain_start = time.time()
            for _ in range(20):
                # Check overall timeout
                if time.time() - drain_start > CONFIG_DRAIN_TIMEOUT:
                    logger.warning("Config drain loop timeout - continuing with partial config")
                    break
                try:
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=0.3)
                    text = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else msg

                    # Only check the FIRST badp message (auth response)
                    if not auth_checked and "MSG badp=" in text:
                        if "badp=0" in text:
                            logger.debug("Authentication successful")
                            auth_checked = True
                        else:
                            logger.error("Authentication failed (bad password)")
                            return False

                    # v1.2.0: Parse config messages for full device config
                    # Web-888 sends "MSG load_cfg=" and "MSG load_adm="
                    if "MSG load_cfg=" in text or "MSG cfg=" in text:
                        self._parse_cfg_message(text)
                    if "MSG load_adm=" in text:
                        self._parse_adm_message(text)
                    # v1.2.1: Parse config_cb for MAC address and serial number
                    if "MSG config_cb=" in text:
                        self._parse_config_cb(text)

                    # Stop draining after config is loaded
                    if "cfg_loaded" in text:
                        break
                except asyncio.TimeoutError:
                    break

            # v1.2.1: Validate auth succeeded if password was provided
            if auth_required and not auth_checked:
                logger.error("Authentication response not received - connection may be unauthorized")
                await self._ws.close()
                return False

            # v1.2.1: Request config_cb for MAC address and device identity
            # This sends MSG config_cb= with MAC, serial number, and DNA
            await self._ws.send("SET GET_CONFIG")
            try:
                for _ in range(10):
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=0.3)
                    text = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else msg
                    if "MSG config_cb=" in text:
                        self._parse_config_cb(text)
                        break
            except asyncio.TimeoutError:
                logger.debug("config_cb not received (optional)")

            # v1.1.0 Hybrid mode: fetch HTTP /status for device metadata
            # (name, location, version, antenna, bands, sdr_hw, etc.)
            # WebSocket doesn't provide this info, only stats_cb/user_cb
            logger.debug("Fetching HTTP /status for device metadata (hybrid mode)")
            await self._fetch_http_status()

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
                # Request stats and users via WebSocket
                await self._ws.send("SET STATS_UPD ch=0")
                await asyncio.sleep(0.5)
                await self._ws.send("SET GET_USERS")
                await asyncio.sleep(0.5)
                await self._ws.send("SET gps_update")

                # v1.1.0 Hybrid mode: also fetch HTTP /status to refresh
                # HTTP-only data (snr, fixes_min, fixes_hour, etc.)
                await self._fetch_http_status()

                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"WS poll error: {e}")
                self.status.connected = False
                break  # Exit loop on error, let reconnect handle it

    async def _ws_receive_loop(self):
        """Process incoming WebSocket messages."""
        import websockets

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    self._parse_ws_message(message)
                    self.status.last_update = time.time()

                    # v1.2.1: Isolate callback errors - don't let HA sensor errors kill connection
                    if self.on_update:
                        try:
                            self.on_update(self.status)
                        except Exception as cb_err:
                            logger.error(f"on_update callback error (connection unaffected): {cb_err}")

        except asyncio.CancelledError:
            logger.debug("WebSocket receive loop cancelled")
        except websockets.exceptions.ConnectionClosedError as e:
            # v1.1.0: Specific handling for WebSocket close errors
            logger.warning(f"WebSocket closed unexpectedly: code={e.code} reason={e.reason}")
            self.status.connected = False
        except websockets.exceptions.ConnectionClosedOK:
            # Normal close - not an error
            logger.debug("WebSocket closed normally")
            self.status.connected = False
        except Exception as e:
            # Generic fallback - log full error for debugging
            logger.error(f"WebSocket receive error: {type(e).__name__}: {e}")
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
            msg_value = content[eq_idx + 1 :]

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
                preemptible = False

                if "decoded" in status_str:
                    try:
                        decoded_count = int(status_str.split()[0])
                    except (ValueError, IndexError):
                        pass

                # v1.2.1: Check for preemptible flag (e.g., "13693 decoded, preemptible")
                if "preemptible" in status_str.lower():
                    preemptible = True

                channel = ChannelInfo(
                    index=ch.get("i", 0),
                    name=ch.get("n", ""),
                    frequency_hz=ch.get("f", 0),
                    mode=ch.get("m", ""),
                    extension=ch.get("e", ""),
                    decoded_count=decoded_count,
                    client_ip=ch.get("a", ""),
                    session_time=ch.get("t", ""),
                    preemptible=preemptible,
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
            # v1.2.1: Sequence and realtime errors (from stats "0 sequence, 0 realtime")
            self.status.system.sequence_errors = data.get("as", 0)
            self.status.system.realtime_errors = data.get("ar", 0)

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

    def _parse_cfg_message(self, text: str):
        """Parse MSG cfg= or MSG load_cfg= message for reporter config.

        Web-888/KiwiSDR sends config during auth handshake. We extract:
        - Reporter callsign and grid square
        - SNR/dT corrections
        - Autorun slot configuration (which channels run FT8/WSPR)
        """
        try:
            # Extract JSON from MSG load_cfg= or MSG cfg=
            if "MSG load_cfg=" in text:
                cfg_start = text.find("MSG load_cfg=") + len("MSG load_cfg=")
            elif "MSG cfg=" in text:
                cfg_start = text.find("MSG cfg=") + len("MSG cfg=")
            else:
                return

            cfg_json = text[cfg_start:].strip()

            # Log raw cfg for debugging format issues
            logger.debug(f"Raw cfg message (first 200 chars): {cfg_json[:200]}")

            # URL decode if needed
            cfg_json = unquote(cfg_json)
            logger.debug(f"Decoded cfg (first 500 chars): {cfg_json[:500]}")

            data = json.loads(cfg_json)
            logger.debug(f"Parsed cfg keys: {list(data.keys())[:20]}")

            # Web-888 config structure:
            # - WSPR section: callsign, grid (for wsprnet.org)
            # - ft8 section: callsign, grid, SNR_adj, dT_adj (for PSKReporter)
            # FT8 callsign/grid are often empty and use WSPR values as fallback

            # Get WSPR callsign/grid (primary identity, used for wsprnet.org)
            wspr_section = data.get("WSPR", data.get("wspr", {}))
            if wspr_section:
                self.status.reporter.wspr_callsign = wspr_section.get("callsign", "")
                self.status.reporter.wspr_grid = wspr_section.get("grid", "")
                logger.debug(
                    f"Found WSPR config: callsign={self.status.reporter.wspr_callsign}, "
                    f"grid={self.status.reporter.wspr_grid}"
                )

            # Get FT8 callsign/grid and corrections (for PSKReporter)
            ft8_section = data.get("ft8", data.get("FT8", {}))
            if ft8_section:
                self.status.reporter.ft8_callsign = ft8_section.get("callsign", "")
                self.status.reporter.ft8_grid = ft8_section.get("grid", "")
                snr_corr = ft8_section.get("SNR_adj", ft8_section.get("SNR_correction", 0))
                dt_corr = ft8_section.get("dT_adj", ft8_section.get("dT_correction", 0))
                self.status.reporter.snr_correction = int(snr_corr) if snr_corr else 0
                self.status.reporter.dt_correction = int(dt_corr) if dt_corr else 0
                logger.debug(
                    f"Found ft8 config: callsign={self.status.reporter.ft8_callsign}, "
                    f"SNR_adj={snr_corr}, dT_adj={dt_corr}"
                )

            # Fallbacks for grid (rx_grid at top level, or index_html_params.RX_QRA)
            if not self.status.reporter.wspr_grid:
                if "rx_grid" in data:
                    self.status.reporter.wspr_grid = data["rx_grid"]
                    logger.debug(f"Found rx_grid in load_cfg: {self.status.reporter.wspr_grid}")
                elif "index_html_params" in data:
                    self.status.reporter.wspr_grid = data["index_html_params"].get("RX_QRA", "")

            # Log effective callsign (what will be used for reporting)
            if self.status.reporter.callsign:
                logger.info(f"Effective reporter callsign: {self.status.reporter.callsign}")
            else:
                logger.debug("No reporter callsign found in cfg message")

            # Parse autorun configuration from WSPR/FT8 sections
            # Format: WSPR.autorun0, WSPR.autorun1, ... (band codes, 0=disabled)
            # Band codes: 2=160m, 3=80m, 4=60m, 5=40m, 6=30m, 7=20m, 8=17m,
            #            9=15m, 10=12m, 11=10m, 12=6m, 13=2m, 14=630m, 15=2200m, 16=FT4, 17=60EU
            wspr_autorun = []
            ft8_autorun = []

            # Get WSPR autorun from WSPR section
            wspr_section = data.get("WSPR", data.get("wspr", {}))
            if wspr_section:
                for i in range(12):
                    band_code = wspr_section.get(f"autorun{i}", 0)
                    wspr_autorun.append(band_code)

            # Get FT8 autorun from ft8 section
            ft8_section = data.get("ft8", data.get("FT8", {}))
            if ft8_section:
                for i in range(12):
                    band_code = ft8_section.get(f"autorun{i}", 0)
                    ft8_autorun.append(band_code)

            # Store autorun info for both modes
            if wspr_autorun:
                self.status.reporter.autorun = wspr_autorun
                active_wspr = sum(1 for b in wspr_autorun if b > 0)
                logger.info(f"Parsed WSPR autorun: {active_wspr} active channels")
            if ft8_autorun:
                self.status.reporter.ft8_autorun = ft8_autorun
                active_ft8 = sum(1 for b in ft8_autorun if b > 0)
                logger.info(f"Parsed FT8 autorun: {active_ft8} active channels")

            # === Parse DeviceConfig from load_cfg ===
            cfg = self.status.config

            # Calibration
            cfg.s_meter_cal = data.get("S_meter_cal", 0)
            cfg.waterfall_cal = data.get("waterfall_cal", 0)
            cfg.dc_offset_i = data.get("DC_offset_I", 0.0)
            cfg.dc_offset_q = data.get("DC_offset_Q", 0.0)
            cfg.clk_adj = data.get("clk_adj", 0)
            cfg.adc_clk_corr = data.get("ADC_clk2_corr", 0)
            cfg.overload_mute = data.get("overload_mute", 0)

            # Feature flags
            drm = data.get("DRM", {})
            cfg.drm_enabled = drm.get("enable", False) if isinstance(drm, dict) else False
            cfg.wspr_enabled = wspr_section.get("enable", False) if wspr_section else False
            cfg.wspr_spot_log = wspr_section.get("spot_log", False) if wspr_section else False
            cfg.wspr_syslog = wspr_section.get("syslog", False) if wspr_section else False
            cfg.wspr_gps_update_grid = wspr_section.get("GPS_update_grid", False) if wspr_section else False
            cfg.spectral_inversion = data.get("spectral_inversion", False)
            cfg.ext_adc_clk = data.get("ext_ADC_clk", False)
            cfg.no_waterfall = data.get("no_wf", False)

            # Session/access config
            cfg.inactivity_timeout_mins = data.get("inactivity_timeout_mins", 0)
            cfg.ip_limit_mins = data.get("ip_limit_mins", 0)
            cfg.chan_no_pwd = data.get("chan_no_pwd", 0)
            cfg.n_camp = data.get("n_camp", 0)
            cfg.ext_api_nchans = data.get("ext_api_nchans", 0)
            cfg.tdoa_nchans = data.get("tdoa_nchans", -1)

            # Noise reduction
            cfg.nb_algo = data.get("nb_algo", 0)
            cfg.nb_thresh = data.get("nb_thresh", 0)
            cfg.nb_gate = data.get("nb_gate", 0)
            cfg.nr_algo = data.get("nr_algo", 0)

            # Device info
            cfg.rx_name = data.get("rx_name", "")
            cfg.rx_device = data.get("rx_device", "")
            cfg.rx_location = data.get("rx_location", "")
            cfg.rx_antenna = data.get("rx_antenna", "")
            cfg.rx_asl = data.get("rx_asl", 0)
            cfg.rx_gps = data.get("rx_gps", "")
            cfg.owner_info = data.get("owner_info", "")
            cfg.admin_email = data.get("admin_email", "")
            tdoa = data.get("tdoa", {})
            cfg.tdoa_server = tdoa.get("server", "") if isinstance(tdoa, dict) else ""

            logger.info(f"Parsed device config: {cfg.rx_name}, {cfg.rx_device}")

        except json.JSONDecodeError as e:
            logger.debug(f"cfg JSON parse error: {e}")
        except Exception as e:
            logger.debug(f"cfg parse error: {e}")

    def _parse_adm_message(self, text: str):
        """Parse MSG load_adm= message for admin configuration.

        This contains network settings, security options, and service flags.
        """
        try:
            if "MSG load_adm=" not in text:
                return

            adm_start = text.find("MSG load_adm=") + len("MSG load_adm=")
            adm_json = text[adm_start:].strip()
            adm_json = unquote(adm_json)
            data = json.loads(adm_json)
            logger.debug(f"Parsed adm keys: {list(data.keys())[:15]}")

            cfg = self.status.config

            # Admin feature flags
            cfg.enable_gps = data.get("enable_gps", True)
            cfg.gps_corr = data.get("gps_corr", True)
            cfg.airband = data.get("airband", False)
            cfg.narrowband = data.get("narrowband", False)
            cfg.wf_share = data.get("wf_share", False)
            cfg.server_enabled = data.get("server_enabled", True)
            cfg.use_ssl = data.get("use_ssl", False)
            cfg.sdr_hu_register = data.get("sdr_hu_register", False)
            cfg.kiwisdr_com_register = data.get("kiwisdr_com_register", False)
            cfg.ip_blacklist_auto = data.get("ip_blacklist_auto_download", False)
            cfg.ip_blacklist_mtime = data.get("ip_blacklist_mtime", 0)

            # Network config
            ip_cfg = data.get("ip_address", {})
            if isinstance(ip_cfg, dict):
                cfg.configured_ip = ip_cfg.get("ip", "")
                cfg.use_static_ip = ip_cfg.get("use_static", False)
                cfg.netmask = ip_cfg.get("netmask", "")
                cfg.gateway = ip_cfg.get("gateway", "")
                # v1.2.1: Auto-discover MAC address from admin config
                mac = ip_cfg.get("mac", "") or ip_cfg.get("mac_address", "")
                if mac:
                    cfg.mac_address = mac
                    logger.info(f"Auto-discovered MAC address: {mac}")
            cfg.port = data.get("port", 8073)

            # v1.2.1: Also check for MAC at top level (some firmware versions)
            if not cfg.mac_address:
                mac = data.get("mac", "") or data.get("mac_address", "") or data.get("ethernet_mac", "")
                if mac:
                    cfg.mac_address = mac
                    logger.info(f"Auto-discovered MAC address (top-level): {mac}")

            logger.info(f"Parsed admin config: GPS={cfg.enable_gps}, server={cfg.server_enabled}")

        except json.JSONDecodeError as e:
            logger.debug(f"adm JSON parse error: {e}")
        except Exception as e:
            logger.debug(f"adm parse error: {e}")

    def _parse_config_cb(self, text: str):
        """Parse MSG config_cb= message for device identity.

        This contains MAC address, serial number, and hardware DNA.
        Response to SET GET_CONFIG command.

        Format: {"r":12,"g":32,"s":24120097,"pu":"1.2.3.4","pe":8073,
                 "pv":"10.1.1.28","pi":8073,"n":24,"m":"6a:8c:58:18:61:f0",
                 "v1":2024,"v2":1130,"d1":3,"d2":20,"dna":"..."}
        """
        try:
            if "MSG config_cb=" not in text:
                return

            cb_start = text.find("MSG config_cb=") + len("MSG config_cb=")
            cb_json = text[cb_start:].strip()
            data = json.loads(cb_json)

            cfg = self.status.config

            # v1.2.1: Extract device identity
            mac = data.get("m", "")
            if mac:
                cfg.mac_address = mac.upper()
                logger.info(f"Auto-discovered MAC address: {cfg.mac_address}")

            serno = data.get("s", "")
            if serno:
                cfg.serial_number = str(serno)
                logger.info(f"Device serial number: {cfg.serial_number}")

            dna = data.get("dna", "")
            if dna:
                cfg.dna = dna
                logger.debug(f"Device DNA: {cfg.dna}")

        except json.JSONDecodeError as e:
            logger.debug(f"config_cb JSON parse error: {e}")
        except Exception as e:
            logger.debug(f"config_cb parse error: {e}")


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
        print(
            f"[Update] CPU: {status.system.cpu_temp_c}°C, "
            f"Channels: {len(status.channels)}, "
            f"GPS: {status.gps.grid_square}"
        )

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
            print(
                f"  RX{ch.index}: {ch.name} @ {ch.frequency_khz:.2f} kHz "
                f"({ch.extension}) - {ch.decoded_count} decoded"
            )

        await client.disconnect()
    else:
        print("Failed to connect")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
