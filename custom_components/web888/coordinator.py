"""DataUpdateCoordinator for Web-888 SDR Monitor."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ENABLE_CHANNELS,
    CONF_HOST,
    CONF_MAC,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONNECTION_TIMEOUT,
    DEFAULT_ENABLE_CHANNELS,
    DEFAULT_MODE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_AUTO,
    MODE_HTTP,
    MODE_WEBSOCKET,
    NUM_CHANNELS,
)
from .web888_client import Web888Client, Web888Status

_LOGGER = logging.getLogger(__name__)


class Web888Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage Web-888 SDR data fetching."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.password = entry.data.get(CONF_PASSWORD, "")
        self.mac = entry.data.get(CONF_MAC, "")
        self.enable_channels = entry.options.get(
            CONF_ENABLE_CHANNELS,
            entry.data.get(CONF_ENABLE_CHANNELS, DEFAULT_ENABLE_CHANNELS),
        )

        # Determine connection mode
        config_mode = entry.options.get(CONF_MODE, entry.data.get(CONF_MODE, DEFAULT_MODE))
        if config_mode == MODE_AUTO:
            # Auto-detect: WebSocket if password provided, otherwise HTTP
            self.mode = MODE_WEBSOCKET if self.password else MODE_HTTP
        else:
            self.mode = config_mode

        # Get scan interval from options (allows changing without reconfiguration)
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        # Create client instance
        self._client = Web888Client(
            host=self.host,
            port=self.port,
            mode=self.mode,
            password=self.password,
            poll_interval=scan_interval,
        )

        # Track connection state
        self._connected = False
        self._last_status: Web888Status | None = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for Home Assistant device registry."""
        identifiers = {(DOMAIN, self.entry.entry_id)}

        # Add MAC as additional identifier if provided
        if self.mac:
            mac_formatted = self.mac.upper().replace("-", ":")
            identifiers.add((DOMAIN, mac_formatted))

        info = {
            "identifiers": identifiers,
            "name": self._last_status.name if self._last_status else f"Web-888 ({self.host})",
            "manufacturer": "RX-888 Team",
            "model": "Web-888 SDR",
            "sw_version": self._last_status.sw_version if self._last_status else "Unknown",
            "configuration_url": f"http://{self.host}:{self.port}",
        }

        # Add MAC as connection for device linking
        if self.mac:
            mac_formatted = self.mac.upper().replace("-", ":")
            info["connections"] = {("mac", mac_formatted)}

        return info

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Web-888 SDR."""
        try:
            # Connect if not connected
            if not self._connected:
                _LOGGER.debug("Connecting to Web-888 at %s:%s (mode: %s)", self.host, self.port, self.mode)
                if not await asyncio.wait_for(self._client.connect(), timeout=CONNECTION_TIMEOUT):
                    raise UpdateFailed(f"Failed to connect to Web-888 at {self.host}:{self.port}")
                self._connected = True
                _LOGGER.info("Connected to Web-888 at %s:%s", self.host, self.port)

            # For HTTP mode, fetch fresh status
            if self.mode == MODE_HTTP:
                await asyncio.wait_for(self._client._fetch_http_status(), timeout=CONNECTION_TIMEOUT)

            # Get current status
            status = self._client.status
            self._last_status = status

            # Build data dictionary
            data: dict[str, Any] = {
                # Connection info
                "connected": status.connected,
                "mode": status.mode,
                "last_update": status.last_update,

                # Device info
                "name": status.name,
                "location": status.location,
                "sw_version": status.sw_version,
                "antenna": status.antenna,

                # Basic sensors
                "users": status.users,
                "users_max": status.users_max,
                "uptime_seconds": status.uptime_seconds,
                "uptime_formatted": status.uptime_formatted,

                # GPS sensors (fixes available in HTTP, satellites/grid only in WebSocket)
                "gps_fixes": status.gps.fixes,
                "gps_satellites": len(status.gps.satellites) if status.gps.satellites else (
                    None if self.mode == MODE_HTTP else 0
                ),
                "gps_lock": status.gps.fixes > 0,  # Lock = has received fixes
                "grid_square": status.gps.grid_square or (None if self.mode == MODE_HTTP else ""),
                "latitude": status.gps.latitude or (None if self.mode == MODE_HTTP else 0.0),
                "longitude": status.gps.longitude or (None if self.mode == MODE_HTTP else 0.0),

                # WebSocket-only sensors (None in HTTP mode)
                "cpu_temp_c": status.system.cpu_temp_c if self.mode != MODE_HTTP else None,
                "audio_bandwidth": (
                    int(status.system.audio_kbps * 1000) if status.system.audio_kbps else 0
                ) if self.mode != MODE_HTTP else None,

                # Calculate total decodes across all channels (WebSocket only)
                "total_decodes": (
                    sum(ch.decoded_count for ch in status.channels) if status.channels else 0
                ) if self.mode != MODE_HTTP else None,

                # Channels (if enabled)
                "channels": [],
            }

            # Add per-channel data if enabled
            if self.enable_channels and status.channels:
                for i in range(NUM_CHANNELS):
                    if i < len(status.channels):
                        ch = status.channels[i]
                        data["channels"].append({
                            "index": ch.index,
                            "name": ch.name,
                            "frequency_hz": ch.frequency_hz,
                            "mode": ch.mode,
                            "decoded_count": ch.decoded_count,
                            "active": True,
                        })
                    else:
                        # Empty channel slot
                        data["channels"].append({
                            "index": i,
                            "name": "",
                            "frequency_hz": 0,
                            "mode": "",
                            "decoded_count": 0,
                            "active": False,
                        })

            return data

        except asyncio.TimeoutError as err:
            self._connected = False
            raise UpdateFailed(f"Timeout connecting to Web-888 at {self.host}:{self.port}") from err
        except Exception as err:
            self._connected = False
            _LOGGER.exception("Error fetching data from Web-888")
            raise UpdateFailed(f"Error communicating with Web-888: {err}") from err

    async def async_shutdown(self) -> None:
        """Disconnect from Web-888 on shutdown."""
        if self._client:
            await self._client.disconnect()
            self._connected = False
            _LOGGER.info("Disconnected from Web-888 at %s", self.host)
