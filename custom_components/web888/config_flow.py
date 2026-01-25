"""Config flow for Web-888 SDR Monitor integration."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENABLE_CHANNELS,
    CONF_ENABLE_SATELLITES,
    CONF_HOST,
    CONF_MAC,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PSKR_CALLSIGN,
    CONF_SCAN_INTERVAL,
    CONF_THERMAL_THRESHOLD,
    CONNECTION_TIMEOUT,
    DEFAULT_ENABLE_CHANNELS,
    DEFAULT_ENABLE_SATELLITES,
    DEFAULT_MODE,
    DEFAULT_PORT,
    DEFAULT_PSKR_CALLSIGN,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_THERMAL_THRESHOLD,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MODE_AUTO,
    MODE_HTTP,
    MODE_WEBSOCKET,
)

_LOGGER = logging.getLogger(__name__)

# MAC address validation pattern
MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


def validate_mac(mac: str) -> str | None:
    """Validate MAC address format. Empty is valid."""
    mac = mac.strip()
    if mac and not MAC_REGEX.match(mac):
        return "invalid_mac"
    return None


async def test_connection(host: str, port: int, password: str = "") -> tuple[bool, str]:
    """Test connection to Web-888 SDR.

    Returns (success, error_key) tuple.
    """
    # First test HTTP connection (always available)
    url = f"http://{host}:{port}/status"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=CONNECTION_TIMEOUT)
            ) as resp:
                if resp.status != 200:
                    return False, "cannot_connect"
                # Parse status to verify it's a Web-888
                # v1.2.1: Use OR - require BOTH fields present (stricter validation)
                text = await resp.text()
                if "offline=" not in text.lower() or "users=" not in text.lower():
                    return False, "not_web888"
    except asyncio.TimeoutError:
        return False, "timeout"
    except aiohttp.ClientError:
        return False, "cannot_connect"
    except Exception:  # noqa: BLE001
        return False, "unknown"

    # If password provided, test WebSocket auth
    if password:
        try:
            from .web888_client import Web888Client

            client = Web888Client(host, port, mode="websocket", password=password)
            if not await asyncio.wait_for(client.connect(), timeout=CONNECTION_TIMEOUT):
                await client.disconnect()
                return False, "invalid_auth"
            await client.disconnect()
        except asyncio.TimeoutError:
            return False, "timeout"
        except ImportError:
            # v1.2.1: If client module fails to import, we can't validate auth
            _LOGGER.error("Could not import web888_client for auth test")
            return False, "unknown"
        except Exception:  # noqa: BLE001
            return False, "invalid_auth"

    return True, ""


class Web888ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Web-888 SDR Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            password = user_input.get(CONF_PASSWORD, "")
            mac = user_input.get(CONF_MAC, "").strip()

            # Validate MAC format
            if error := validate_mac(mac):
                errors["base"] = error
            else:
                # Test connection
                success, error = await test_connection(host, port, password)
                if not success:
                    errors["base"] = error
                else:
                    # Create unique ID from host
                    unique_id = f"web888_{host.replace('.', '_')}_{port}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Format MAC for storage
                    mac_formatted = mac.upper().replace("-", ":") if mac else ""

                    return self.async_create_entry(
                        title=f"Web-888 ({host})",
                        data={
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_PASSWORD: password,
                            CONF_MAC: mac_formatted,
                            CONF_MODE: DEFAULT_MODE,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                            CONF_ENABLE_CHANNELS: user_input.get(
                                CONF_ENABLE_CHANNELS, DEFAULT_ENABLE_CHANNELS
                            ),
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                    vol.Optional(CONF_PASSWORD, default=""): str,
                    vol.Optional(CONF_MAC, default=""): str,
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(CONF_ENABLE_CHANNELS, default=DEFAULT_ENABLE_CHANNELS): bool,
                }
            ),
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_options_flow(cls, config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return Web888OptionsFlow(config_entry)


class Web888OptionsFlow(OptionsFlowWithConfigEntry):
    """Handle options flow for Web-888 SDR Monitor."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values (self.config_entry provided by base class)
        entry = self.config_entry
        current = {
            CONF_SCAN_INTERVAL: entry.options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
            CONF_MODE: entry.options.get(
                CONF_MODE,
                entry.data.get(CONF_MODE, DEFAULT_MODE),
            ),
            CONF_ENABLE_CHANNELS: entry.options.get(
                CONF_ENABLE_CHANNELS,
                entry.data.get(CONF_ENABLE_CHANNELS, DEFAULT_ENABLE_CHANNELS),
            ),
            # v1.1.0: New options
            CONF_ENABLE_SATELLITES: entry.options.get(
                CONF_ENABLE_SATELLITES,
                entry.data.get(CONF_ENABLE_SATELLITES, DEFAULT_ENABLE_SATELLITES),
            ),
            CONF_THERMAL_THRESHOLD: entry.options.get(
                CONF_THERMAL_THRESHOLD,
                entry.data.get(CONF_THERMAL_THRESHOLD, DEFAULT_THERMAL_THRESHOLD),
            ),
            CONF_PSKR_CALLSIGN: entry.options.get(
                CONF_PSKR_CALLSIGN,
                entry.data.get(CONF_PSKR_CALLSIGN, DEFAULT_PSKR_CALLSIGN),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current[CONF_SCAN_INTERVAL],
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_MODE,
                        default=current[CONF_MODE],
                    ): vol.In(
                        {
                            MODE_AUTO: "Auto (WebSocket if password, else HTTP)",
                            MODE_HTTP: "HTTP only (no authentication)",
                            MODE_WEBSOCKET: "WebSocket (requires password)",
                        }
                    ),
                    vol.Optional(
                        CONF_ENABLE_CHANNELS,
                        default=current[CONF_ENABLE_CHANNELS],
                    ): bool,
                    # v1.1.0: New options
                    vol.Optional(
                        CONF_ENABLE_SATELLITES,
                        default=current[CONF_ENABLE_SATELLITES],
                        description={
                            "suggested_value": "Enable per-satellite sensors for security monitoring"
                        },
                    ): bool,
                    vol.Optional(
                        CONF_THERMAL_THRESHOLD,
                        default=current[CONF_THERMAL_THRESHOLD],
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=50, max=100),
                    ),
                    vol.Optional(
                        CONF_PSKR_CALLSIGN,
                        default=current[CONF_PSKR_CALLSIGN],
                        description={"suggested_value": "Callsign for PSKReporter correlation"},
                    ): str,
                }
            ),
        )
