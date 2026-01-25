# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-01-25

### Fixed

- **EntityCategory.CONFIG Error** - Changed `EntityCategory.CONFIG` to `EntityCategory.DIAGNOSTIC` for all v1.2.0 feature flag binary sensors and session config sensors. Home Assistant does not allow CONFIG category for sensor/binary_sensor entities - only DIAGNOSTIC is valid for read-only entities.
  - Affected binary sensors: GPS Enabled, GPS Correction, DRM Enabled, WSPR Enabled, WSPR Spot Logging, WSPR Auto-Update Grid, Server Enabled, Airband Mode, Static IP Mode, SDR.hu Listed, KiwiSDR.com Listed
  - Affected sensors: Inactivity Timeout, Password-Free Channels, Camping Slots, API Channels

- **WebSocket Disconnection Handling** - Improved WebSocket connection stability:
  - Enabled keep-alive pings (`ping_interval=20`, `ping_timeout=10`) to detect dead connections
  - Added coordinator state sync - coordinator now detects when client reports disconnected and triggers reconnect
  - Reduces "code=1006" (abnormal closure) errors that caused sensors to become unavailable

- **WebSocket Authentication Validation** - Now validates that authentication actually succeeded before continuing. Previously, if the auth response wasn't received within the drain loop, connection would proceed as if authenticated.

- **Config Flow Import Error** - Fixed missing return statement after ImportError in password validation. Previously, if the web888_client module failed to import, auth test was silently skipped.

- **Callback Error Isolation** - Wrapped `on_update` callbacks in try/except to prevent Home Assistant sensor update errors from disconnecting the WebSocket client.

- **Thermal Warning Null Check** - Fixed thermal warning check using `is not None` instead of truthy evaluation. Previously, CPU temp of exactly 0°C would incorrectly skip the warning check.

- **HTTP Session Management** - Implemented connection pooling by reusing aiohttp ClientSession instead of creating a new session per request. Session is now properly closed on disconnect.

- **Public API for HTTP Status** - Changed `_fetch_http_status()` to public `fetch_http_status()` method. Private name kept as alias for backward compatibility.

- **Web-888 Device Detection** - Changed device validation logic from AND to OR - now requires BOTH `offline=` and `users=` fields to be present (stricter validation prevents non-Web-888 devices from being added).

- **Config Drain Loop Timeout** - Added 5-second overall timeout for the initial WebSocket config message drain loop. Previously, slow connections could hang for up to 6 seconds.

- **Timeout Constants** - Replaced hardcoded timeout values with named constants (`HTTP_TIMEOUT`, `WS_PING_INTERVAL`, `WS_PING_TIMEOUT`, `WS_CLOSE_TIMEOUT`, `CONFIG_DRAIN_TIMEOUT`) for maintainability.

- **Satellite Sensor Availability** - Fixed satellite sensors showing as "unavailable" when fewer than 12 satellites are tracked. Array is now padded to MAX_SATELLITES (12) with placeholder entries for untracked slots. Added `tracked` attribute to distinguish active satellites.

### Added

- **MAC Address Auto-Discovery** - Automatically discovers MAC address, serial number, and hardware DNA from WebSocket `config_cb` message when admin mode is connected. No manual MAC entry needed for device registry linking. Falls back to user-provided MAC if auto-discovery unavailable.

- **New Diagnostic Sensors** (WebSocket only):
  - **Sequence Errors** - Sequence error counter from device stats
  - **Realtime Errors** - Realtime error counter from device stats
  - **Total Session Hours** - Combined runtime of all active channels (hours)
  - **Preemptible Channels** - Count of channels that can be preempted by users

- **Enhanced Channel Attributes** - Per-channel sensors now include:
  - `session_time` - Channel runtime in HH:MM:SS format (e.g., "518:00:56")
  - `session_seconds` - Channel runtime in seconds (for automations)
  - `preemptible` - Whether the channel can be preempted by users

## [1.2.0] - 2026-01-25

### Added

#### Full Device Configuration Exposure (WebSocket Only)

All device configuration is now parsed from WebSocket `load_cfg` and `load_adm` messages and exposed as sensors.

##### Calibration Sensors (Diagnostic)
- **S-Meter Calibration** - S-meter offset (dB)
- **Waterfall Calibration** - Waterfall offset (dB)
- **DC Offset I/Q** - ADC DC offset correction
- **Clock Adjustment** - Clock trim value
- **ADC Clock Correction** - ADC clock frequency correction
- **Overload Mute** - Overload mute threshold (dB)

##### Session/Access Config Sensors
- **Inactivity Timeout** - Auto-disconnect timeout (minutes)
- **IP Rate Limit** - Per-IP connection rate limit (minutes)
- **Password-Free Channels** - Channels without password requirement
- **Camping Slots** - Number of camping slots allowed
- **API Channels** - Channels for external API access
- **TDoA Channels** - Channels for TDoA operations

##### Network Config Sensors
- **Configured IP** - Static IP if configured
- **Service Port** - Web service port

##### Device Info Sensors
- **Device Location** - Location string from config
- **Antenna Description** - Antenna info from config
- **Altitude ASL** - Altitude above sea level (meters)
- **Owner Info** - Owner contact email
- **Admin Email** - Admin contact email

##### Feature Flag Binary Sensors (Diagnostic Category)
- **GPS Enabled** - Whether GPS is enabled
- **GPS Correction** - GPS frequency correction enabled
- **DRM Enabled** - Digital Radio Mondiale extension enabled
- **WSPR Enabled** - WSPR extension enabled
- **WSPR Spot Logging** - WSPR spot logging to file
- **WSPR Auto-Update Grid** - Auto-update grid from GPS
- **Server Enabled** - KiwiSDR server mode enabled
- **Airband Mode** - Airband receive mode
- **Static IP Mode** - Using static IP configuration
- **SDR.hu Listed** - Registered with SDR.hu directory
- **KiwiSDR.com Listed** - Registered with KiwiSDR.com

### Changed

- **Separate WSPR and FT8 Reporter Fields**: Reporter callsign/grid now stored separately for WSPR and FT8
  - `wspr_callsign`, `wspr_grid` - For wsprnet.org reporting
  - `ft8_callsign`, `ft8_grid` - For PSKReporter (often empty, falls back to WSPR)
  - Computed properties provide effective callsign/grid (FT8 if set, else WSPR)

### Technical Notes

- New `DeviceConfig` dataclass with ~50 configuration fields
- Parses both `MSG load_cfg=` (main config) and `MSG load_adm=` (admin config)
- Feature flags use `EntityCategory.CONFIG` for HA organization
- Calibration sensors use `EntityCategory.DIAGNOSTIC`
- All config sensors are `websocket_only=True` (admin mode required)
- New sensor count (v1.2.0):
  - Device sensors: ~70 (adds ~15 config sensors)
  - Binary sensors: 17 (adds 11 feature flag sensors)
  - Channel/satellite sensors: unchanged

---

## [1.1.0] - 2026-01-24

### Added

#### New Sensors (WebSocket/Admin Mode)
- **CPU Frequency** - Processor clock speed (MHz)
- **CPU Usage** - Average CPU utilization (%)
- **Waterfall Bandwidth** - Waterfall data rate (B/s)
- **HTTP Bandwidth** - HTTP traffic rate (B/s)
- **Audio Dropped** - Dropped audio packet count
- **Audio Underruns** - Audio buffer underrun events
- **GPS Tracking** - Satellites currently being tracked
- **GPS In Solution** - Satellites used in position fix
- **GPS Avg SNR** - Average satellite signal-to-noise ratio (dB)
- **ADC Clock** - ADC reference clock frequency (MHz)
- **GPS Acquiring** (binary) - Whether GPS is acquiring satellites

#### New Sensors (Both Modes)
- **GPS Fixes/min** - GPS position fixes per minute
- **GPS Fixes/hour** - GPS position fixes per hour
- **Frequency Offset** - Calibration frequency offset (Hz)

#### Thermal Monitoring
- **Thermal Warning** (binary) - Triggers when CPU exceeds threshold
- Configurable threshold via options (default: 70°C)

#### Per-Satellite Sensors (Optional)
- Enable via "Enable Satellite Sensors" option
- Per-satellite metrics: SNR, RSSI, Azimuth, Elevation, In Solution
- Security use case: Detect interference or line-of-sight issues
- Supports up to 12 tracked satellites

#### Reporter Config Auto-Discovery (WebSocket Only)
- **Reporter Callsign** - FT8/WSPR callsign from device config
- **Reporter Grid** - FT8/WSPR grid square from device config
- Auto-parsed from WebSocket config handshake (no manual entry needed)

#### Channel Type Tracking (WebSocket Only)
- **FT8 Channels** - Count of channels running FT8 extension
- **WSPR Channels** - Count of channels running WSPR extension
- **User Channels** - Count of channels with real users connected
- **Idle Channels** - Count of unused channels
- **FT8 Total Decodes** - Combined FT8 decode count across all channels
- **WSPR Total Decodes** - Combined WSPR decode count across all channels
- Per-channel attributes now include `channel_type`, `extension`, `is_extension`, `client_ip`

#### PSKReporter/wsprnet Correlation
- Optional `pskr_callsign` configuration for PSKReporter correlation
- FT8 decodes correlate with PSKReporter spots
- WSPR decodes correlate with wsprnet reports (via wspr-ha-bridge)
- Template sensors for upload efficiency calculations

#### Dashboard Generator
- Web-based dashboard YAML generator (`docs/dashboard-generator.html`)
- Pre-built templates for common layouts
- Example dashboard configurations

### Changed

- **Hybrid Mode**: WebSocket mode now also fetches HTTP `/status` for device metadata
  - Fixes "Unnamed device" issue in Home Assistant device registry
  - Ensures name, location, version, antenna info are always populated
- Improved WebSocket error handling with specific exception types
- Better logging for connection issues and diagnostics

### Fixed

- "Unnamed device" bug - device name now correctly shows in HA
- WebSocket disconnect errors now properly logged with error codes
- Connection state properly tracked on WebSocket close events

### Technical Notes

- New config options: `enable_satellites`, `thermal_threshold`, `pskr_callsign`
- New sensor count (v1.1.0):
  - Device sensors: ~55 (includes reporter config, channel type counts, per-mode decode totals)
  - Binary sensors: 6 (GPS Acquiring, Thermal Warning, Connected, GPS Lock, Antenna, Offline)
  - Channel sensors: 36 (12 channels × 3: frequency, mode, decoded)
  - Satellite sensors: up to 60 (12 satellites × 5 metrics, optional)
- Satellite sensors create 5 entities per tracked satellite (12 max = 60 sensors)
- Channel sensors now include `channel_type` attribute for FT8/WSPR/user/idle classification

## [1.0.0] - 2026-01-04

### Added

- Initial release of Web-888 HA Bridge
- Dual deployment architecture:
  - **Docker/MQTT Bridge**: Standalone container with environment variable configuration
  - **HACS Integration**: Native Home Assistant custom component with ConfigFlow UI
- Support for both HTTP and WebSocket connection modes:
  - HTTP mode: Read-only status polling (no authentication required)
  - WebSocket mode: Full admin data access (requires password)
- Device sensors:
  - Users (active channel count)
  - Uptime
  - CPU Temperature
  - GPS Satellites
  - GPS Fixes
  - Grid Square
  - GPS Position (latitude/longitude)
  - Total Decodes
  - Audio Bandwidth
- Binary sensors:
  - Connected status
  - GPS Lock status
- Per-channel sensors (12 channels):
  - Frequency
  - Mode
  - Decoded count
- MQTT auto-discovery for Home Assistant
- MAC address support for device registry linking
- Exponential backoff reconnection logic (5s -> 60s)
- Comprehensive logging with configurable levels

### Technical Notes

- Requires Python 3.10+
- Compatible with Home Assistant 2024.1.0+
- WebSocket protocol based on KiwiSDR admin interface
