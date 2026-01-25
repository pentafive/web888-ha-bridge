#!/usr/bin/env python3
"""
Web-888 SDR Home Assistant Bridge

Monitors Web-888 SDR receivers and publishes data to Home Assistant via MQTT.
Supports both HTTP-only mode (basic) and WebSocket mode (full data).

Usage:
    docker compose up -d
    # or
    python web888-ha-bridge.py

Environment Variables:
    WEB888_HOST         - Web-888 IP address (required)
    WEB888_PORT         - WebSocket port (default: 8073)
    WEB888_PASSWORD     - Admin password (optional, enables WebSocket mode)
    WEB888_MODE         - "http" or "websocket" (default: auto-detect)
    HA_MQTT_BROKER      - MQTT broker host (required)
    HA_MQTT_PORT        - MQTT broker port (default: 1883)
    HA_MQTT_USER        - MQTT username (optional)
    HA_MQTT_PASS        - MQTT password (optional)
    SCAN_INTERVAL       - Update interval in seconds (default: 30)
    DEVICE_NAME         - Device name in HA (default: Web-888 SDR)
    DEVICE_ID           - Unique device ID (default: generated from host)
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required

import paho.mqtt.client as mqtt

from web888_client import Web888Client, Web888Status

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("web888-ha-bridge")

# Configuration from environment
WEB888_HOST = os.getenv("WEB888_HOST", "")
WEB888_PORT = int(os.getenv("WEB888_PORT", "8073"))
WEB888_MAC = os.getenv("WEB888_MAC", "")  # Optional: for HA device registry
WEB888_PASSWORD = os.getenv("WEB888_PASSWORD", "")
WEB888_MODE = os.getenv("WEB888_MODE", "")  # auto, http, or websocket
HA_MQTT_BROKER = os.getenv("HA_MQTT_BROKER", "")
HA_MQTT_PORT = int(os.getenv("HA_MQTT_PORT", "1883"))
HA_MQTT_USER = os.getenv("HA_MQTT_USER", "")
HA_MQTT_PASS = os.getenv("HA_MQTT_PASS", "")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "30"))
DEVICE_NAME = os.getenv("DEVICE_NAME", "Web-888 SDR")
DEVICE_ID = os.getenv("DEVICE_ID", "")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ENABLE_CHANNEL_SENSORS = os.getenv("ENABLE_CHANNEL_SENSORS", "true").lower() == "true"


def get_device_id(host: str) -> str:
    """Generate a unique device ID from host."""
    if DEVICE_ID:
        return DEVICE_ID
    return f"web888_{host.replace('.', '_')}"


def determine_mode() -> str:
    """Determine client mode based on config."""
    if WEB888_MODE:
        return WEB888_MODE
    # Auto-detect: use websocket if password provided
    return "websocket" if WEB888_PASSWORD else "http"


class MQTTPublisher:
    """Handles MQTT connection and Home Assistant discovery."""

    def __init__(self, broker: str, port: int, username: str = "", password: str = ""):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.connected = False

        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            self.connected = True
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        logger.warning("Disconnected from MQTT broker")
        self.connected = False

    def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_discovery(self, device_id: str, device_name: str, host: str, mode: str, mac: str = ""):
        """Publish Home Assistant MQTT discovery messages."""
        # Build identifiers list - include MAC if provided for UniFi linking
        identifiers = [device_id]
        if mac:
            # Format MAC consistently (uppercase, colon-separated)
            mac_formatted = mac.upper().replace("-", ":")
            identifiers.append(mac_formatted)

        device_info = {
            "identifiers": identifiers,
            "name": device_name,
            "manufacturer": "RX-888 Team",
            "model": "Web-888 SDR",
            "sw_version": "Unknown",
            "configuration_url": f"http://{host}:{WEB888_PORT}",
        }

        # Add connections for MAC (HA uses this for device registry linking)
        if mac:
            device_info["connections"] = [["mac", mac_formatted]]

        # Base sensors (available in both modes)
        sensors = [
            {
                "name": "Users",
                "unique_id": f"{device_id}_users",
                "state_topic": f"web888/{device_id}/status",
                "value_template": "{{ value_json.users }}",
                "icon": "mdi:account-multiple",
                "unit_of_measurement": "users",
            },
            {
                "name": "Uptime",
                "unique_id": f"{device_id}_uptime",
                "state_topic": f"web888/{device_id}/status",
                "value_template": "{{ value_json.uptime }}",
                "icon": "mdi:clock-outline",
            },
            {
                "name": "GPS Fixes",
                "unique_id": f"{device_id}_gps_fixes",
                "state_topic": f"web888/{device_id}/status",
                "value_template": "{{ value_json.gps_fixes }}",
                "icon": "mdi:satellite-variant",
            },
        ]

        # WebSocket-only sensors
        if mode == "websocket":
            sensors.extend([
                {
                    "name": "CPU Temperature",
                    "unique_id": f"{device_id}_cpu_temp",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.cpu_temp }}",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "entity_category": "diagnostic",
                },
                {
                    "name": "Grid Square",
                    "unique_id": f"{device_id}_grid",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.grid }}",
                    "icon": "mdi:map-marker-radius",
                },
                {
                    "name": "GPS Latitude",
                    "unique_id": f"{device_id}_gps_lat",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.gps_lat }}",
                    "icon": "mdi:latitude",
                    "entity_category": "diagnostic",
                },
                {
                    "name": "GPS Longitude",
                    "unique_id": f"{device_id}_gps_lon",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.gps_lon }}",
                    "icon": "mdi:longitude",
                    "entity_category": "diagnostic",
                },
                {
                    "name": "GPS Satellites",
                    "unique_id": f"{device_id}_gps_sats",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.gps_satellites }}",
                    "icon": "mdi:satellite-variant",
                    "unit_of_measurement": "satellites",
                },
                {
                    "name": "Audio Bandwidth",
                    "unique_id": f"{device_id}_audio_bw",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.audio_kbps }}",
                    "icon": "mdi:waveform",
                    "unit_of_measurement": "kB/s",
                    "entity_category": "diagnostic",
                },
                {
                    "name": "Total Decodes",
                    "unique_id": f"{device_id}_total_decodes",
                    "state_topic": f"web888/{device_id}/status",
                    "value_template": "{{ value_json.total_decodes }}",
                    "icon": "mdi:radio-tower",
                },
            ])

        # Publish sensor configs
        for sensor in sensors:
            sensor["device"] = device_info
            config_topic = f"homeassistant/sensor/{sensor['unique_id']}/config"
            self.client.publish(config_topic, json.dumps(sensor), retain=True)
            logger.debug(f"Published discovery: {config_topic}")

        # Binary sensor for connection
        binary_config = {
            "name": "Connected",
            "unique_id": f"{device_id}_connected",
            "state_topic": f"web888/{device_id}/status",
            "value_template": "{{ value_json.connected }}",
            "device_class": "connectivity",
            "payload_on": "true",
            "payload_off": "false",
            "device": device_info,
        }
        self.client.publish(
            f"homeassistant/binary_sensor/{device_id}_connected/config",
            json.dumps(binary_config),
            retain=True,
        )

        # GPS lock binary sensor
        gps_config = {
            "name": "GPS Lock",
            "unique_id": f"{device_id}_gps_lock",
            "state_topic": f"web888/{device_id}/status",
            "value_template": "{{ value_json.gps_lock }}",
            "device_class": "connectivity",
            "payload_on": "true",
            "payload_off": "false",
            "device": device_info,
        }
        self.client.publish(
            f"homeassistant/binary_sensor/{device_id}_gps_lock/config",
            json.dumps(gps_config),
            retain=True,
        )

        logger.info(f"Published MQTT discovery for {device_name} ({mode} mode)")

    def publish_channel_discovery(self, device_id: str, device_info: dict, num_channels: int):
        """Publish per-channel sensor discovery."""
        for i in range(num_channels):
            sensors = [
                {
                    "name": f"Channel {i} Frequency",
                    "unique_id": f"{device_id}_ch{i}_freq",
                    "state_topic": f"web888/{device_id}/channels/{i}",
                    "value_template": "{{ value_json.frequency_khz }}",
                    "icon": "mdi:sine-wave",
                    "unit_of_measurement": "kHz",
                },
                {
                    "name": f"Channel {i} Mode",
                    "unique_id": f"{device_id}_ch{i}_mode",
                    "state_topic": f"web888/{device_id}/channels/{i}",
                    "value_template": "{{ value_json.mode }}",
                    "icon": "mdi:radio",
                },
                {
                    "name": f"Channel {i} Decodes",
                    "unique_id": f"{device_id}_ch{i}_decodes",
                    "state_topic": f"web888/{device_id}/channels/{i}",
                    "value_template": "{{ value_json.decoded_count }}",
                    "icon": "mdi:message-text",
                },
            ]

            for sensor in sensors:
                sensor["device"] = device_info
                config_topic = f"homeassistant/sensor/{sensor['unique_id']}/config"
                self.client.publish(config_topic, json.dumps(sensor), retain=True)

    def publish_status(self, device_id: str, status: Web888Status):
        """Publish status updates to MQTT."""
        # Build status payload
        payload = {
            "connected": str(status.connected).lower(),
            "users": status.users,
            "users_max": status.users_max,
            "uptime": status.uptime_formatted,
            "uptime_seconds": status.uptime_seconds,
            "gps_lock": str(status.gps.fixes > 0).lower(),
            "gps_fixes": status.gps.fixes,
            "name": status.name,
            "version": status.sw_version,
            "last_update": datetime.now(timezone.utc).isoformat(),
        }

        # Add WebSocket-only data if available
        if status.mode == "websocket":
            payload.update({
                "cpu_temp": status.system.cpu_temp_c,
                "cpu_freq": status.system.cpu_freq_mhz,
                "grid": status.gps.grid_square,
                "gps_lat": round(status.gps.latitude, 6),
                "gps_lon": round(status.gps.longitude, 6),
                "gps_satellites": len(status.gps.satellites),
                "audio_kbps": status.system.audio_kbps,
                "total_decodes": sum(ch.decoded_count for ch in status.channels),
            })

        # Publish main status
        self.client.publish(
            f"web888/{device_id}/status",
            json.dumps(payload),
        )

        # Publish per-channel data if available
        for ch in status.channels:
            ch_payload = {
                "index": ch.index,
                "name": ch.name,
                "frequency_hz": ch.frequency_hz,
                "frequency_khz": round(ch.frequency_khz, 2),
                "mode": ch.mode,
                "extension": ch.extension,
                "decoded_count": ch.decoded_count,
            }
            self.client.publish(
                f"web888/{device_id}/channels/{ch.index}",
                json.dumps(ch_payload),
            )

        logger.debug(
            f"Published status: users={status.users}, "
            f"gps={status.gps.fixes}, temp={status.system.cpu_temp_c}°C"
        )


class Web888Bridge:
    """Main bridge class that coordinates SDR client and MQTT publisher."""

    def __init__(self):
        self.running = False
        self.client: Web888Client | None = None
        self.mqtt_publisher: MQTTPublisher | None = None
        self.device_id = ""
        self.mode = ""

    async def start(self):
        """Start the bridge."""
        # Validate configuration
        if not WEB888_HOST:
            logger.error("WEB888_HOST environment variable is required")
            sys.exit(1)
        if not HA_MQTT_BROKER:
            logger.error("HA_MQTT_BROKER environment variable is required")
            sys.exit(1)

        self.device_id = get_device_id(WEB888_HOST)
        self.mode = determine_mode()

        logger.info("Starting Web-888 HA Bridge")
        logger.info(f"  Device ID: {self.device_id}")
        logger.info(f"  Web-888: {WEB888_HOST}:{WEB888_PORT}")
        logger.info(f"  Mode: {self.mode}")
        logger.info(f"  MQTT: {HA_MQTT_BROKER}:{HA_MQTT_PORT}")
        logger.info(f"  Scan interval: {SCAN_INTERVAL}s")

        # Initialize MQTT
        self.mqtt_publisher = MQTTPublisher(
            HA_MQTT_BROKER, HA_MQTT_PORT, HA_MQTT_USER, HA_MQTT_PASS
        )
        if not self.mqtt_publisher.connect():
            logger.error("Failed to connect to MQTT broker")
            sys.exit(1)

        # Wait for MQTT connection
        await asyncio.sleep(1)

        # Publish discovery
        self.mqtt_publisher.publish_discovery(
            self.device_id, DEVICE_NAME, WEB888_HOST, self.mode, WEB888_MAC
        )

        # Initialize Web888 client
        self.client = Web888Client(
            WEB888_HOST,
            WEB888_PORT,
            mode=self.mode,
            password=WEB888_PASSWORD,
            poll_interval=SCAN_INTERVAL,
            on_update=self._on_status_update,
        )

        # Connect
        if not await self.client.connect():
            logger.error("Failed to connect to Web-888")
            sys.exit(1)

        # Start main loop
        self.running = True
        await self._main_loop()

    def _on_status_update(self, status: Web888Status):
        """Callback for real-time status updates (WebSocket mode)."""
        if self.mqtt_publisher and self.mqtt_publisher.connected:
            self.mqtt_publisher.publish_status(self.device_id, status)

    async def _main_loop(self):
        """Main loop - keeps running until stopped."""
        reconnect_delay = 5
        max_reconnect_delay = 60

        while self.running:
            try:
                # Check WebSocket connection health and reconnect if needed
                if self.mode == "websocket" and not self.client.status.connected:
                    logger.info(f"WebSocket disconnected, reconnecting in {reconnect_delay}s...")
                    self.mqtt_publisher.publish_status(self.device_id, self.client.status)
                    await asyncio.sleep(reconnect_delay)

                    if await self.client.connect():
                        logger.info("Reconnected to Web-888")
                        reconnect_delay = 5  # Reset delay on success
                    else:
                        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                        continue

                # In HTTP mode, manually update periodically
                if self.mode == "http":
                    await self.client.update()
                    self.mqtt_publisher.publish_status(self.device_id, self.client.status)

                await asyncio.sleep(SCAN_INTERVAL)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # Publish disconnected status
                self.client.status.connected = False
                self.mqtt_publisher.publish_status(self.device_id, self.client.status)
                await asyncio.sleep(reconnect_delay)

    def stop(self):
        """Stop the bridge."""
        logger.info("Stopping Web-888 HA Bridge")
        self.running = False

        if self.client:
            asyncio.create_task(self.client.disconnect())

        if self.mqtt_publisher:
            # Publish offline status
            if self.client:
                self.client.status.connected = False
                self.mqtt_publisher.publish_status(self.device_id, self.client.status)
            self.mqtt_publisher.disconnect()


async def main():
    """Entry point."""
    bridge = Web888Bridge()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()

    def signal_handler():
        bridge.stop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await bridge.start()
    except KeyboardInterrupt:
        bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
