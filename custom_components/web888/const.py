"""Constants for the Web-888 SDR Monitor integration."""

from typing import Final

DOMAIN: Final = "web888"

# Configuration keys
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_PASSWORD: Final = "password"
CONF_MAC: Final = "mac"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MODE: Final = "mode"
CONF_ENABLE_CHANNELS: Final = "enable_channels"

# Connection modes
MODE_HTTP: Final = "http"
MODE_WEBSOCKET: Final = "websocket"
MODE_AUTO: Final = "auto"

MODE_OPTIONS: Final = [MODE_AUTO, MODE_HTTP, MODE_WEBSOCKET]

# Default settings
DEFAULT_PORT: Final = 8073
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_MODE: Final = MODE_AUTO
DEFAULT_ENABLE_CHANNELS: Final = True

# Device info
MANUFACTURER: Final = "RX-888 Team"
MODEL: Final = "Web-888 SDR"

# Sensor types - Device
SENSOR_USERS: Final = "users"
SENSOR_UPTIME: Final = "uptime"
SENSOR_CPU_TEMP: Final = "cpu_temp"
SENSOR_GPS_SATELLITES: Final = "gps_satellites"
SENSOR_GPS_FIXES: Final = "gps_fixes"
SENSOR_GRID_SQUARE: Final = "grid_square"
SENSOR_LATITUDE: Final = "latitude"
SENSOR_LONGITUDE: Final = "longitude"
SENSOR_TOTAL_DECODES: Final = "total_decodes"
SENSOR_AUDIO_BANDWIDTH: Final = "audio_bandwidth"

# Binary sensor types
BINARY_SENSOR_CONNECTED: Final = "connected"
BINARY_SENSOR_GPS_LOCK: Final = "gps_lock"

# Channel sensor types
SENSOR_CHANNEL_FREQUENCY: Final = "frequency"
SENSOR_CHANNEL_MODE: Final = "mode"
SENSOR_CHANNEL_DECODED: Final = "decoded_count"

# Number of RX channels
NUM_CHANNELS: Final = 12

# Update interval bounds
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 300

# Connection timeout
CONNECTION_TIMEOUT: Final = 10

# Attribution
ATTRIBUTION: Final = "Data from Web-888 SDR"
