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

# v1.1.0: New configuration keys
CONF_ENABLE_SATELLITES: Final = "enable_satellites"
CONF_THERMAL_THRESHOLD: Final = "thermal_threshold"
CONF_PSKR_CALLSIGN: Final = "pskr_callsign"

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

# v1.1.0: New defaults
DEFAULT_ENABLE_SATELLITES: Final = False
DEFAULT_THERMAL_THRESHOLD: Final = 70  # Celsius
DEFAULT_PSKR_CALLSIGN: Final = ""

# Satellite sensor limits
MAX_SATELLITES: Final = 12  # GPS receiver tracks up to 12 satellites

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

# New sensors from /status endpoint
SENSOR_SNR_ALL: Final = "snr_all"
SENSOR_SNR_HF: Final = "snr_hf"
SENSOR_GPS_GOOD: Final = "gps_good"
SENSOR_ALTITUDE: Final = "altitude"
SENSOR_LOCATION: Final = "location"
SENSOR_OPERATOR_EMAIL: Final = "operator_email"
SENSOR_BANDS: Final = "bands"
SENSOR_FREQ_OFFSET: Final = "freq_offset"
SENSOR_ADC_OVERFLOW: Final = "adc_overflow"
SENSOR_DEVICE_STATUS: Final = "device_status"

# Binary sensor types
BINARY_SENSOR_CONNECTED: Final = "connected"
BINARY_SENSOR_GPS_LOCK: Final = "gps_lock"
BINARY_SENSOR_ANTENNA_CONNECTED: Final = "antenna_connected"
BINARY_SENSOR_OFFLINE: Final = "offline"

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

# Reconnect backoff (v1.2.2)
RECONNECT_BACKOFF_BASE: Final = 10      # Base delay (seconds)
RECONNECT_BACKOFF_MAX: Final = 300      # Max delay (seconds)
RECONNECT_BACKOFF_FACTOR: Final = 2     # Exponential multiplier

# Attribution
ATTRIBUTION: Final = "Data from Web-888 SDR"
