# Sensor Reference

Detailed documentation for all sensors provided by Web-888 HA Bridge.

## Availability by Mode

| Sensor Category | HTTP Mode | WebSocket Mode |
|-----------------|-----------|----------------|
| Basic Status (users, uptime) | Yes | Yes |
| GPS Position (fixes, lat/lon) | Yes | Yes |
| SNR Measurements | Yes | Yes |
| Device Status | Yes | Yes |
| CPU Temperature | No | Yes |
| System Diagnostics | No | Yes |
| Channel Sensors | No | Yes |
| Satellite Sensors | No | Yes |
| Reporter Config | No | Yes |
| Device Config | No | Yes |

---

## Basic Status Sensors

### Users
**Entity:** `sensor.web_888_users`
**Unit:** users
**Description:** Number of currently connected users listening to the Web-888.

### Users Max
**Entity:** `sensor.web_888_users_max`
**Unit:** users
**Category:** Diagnostic
**Description:** Maximum simultaneous users allowed.

### Uptime
**Entity:** `sensor.web_888_uptime`
**Unit:** seconds
**Device Class:** duration
**Category:** Diagnostic
**Description:** Time since device boot.

### Connected
**Entity:** `binary_sensor.web_888_connected`
**Type:** Binary
**Device Class:** connectivity
**Description:** Integration connection to the Web-888.

### Offline
**Entity:** `binary_sensor.web_888_offline`
**Type:** Binary
**Device Class:** problem
**Description:** Device offline status.

---

## GPS Sensors

### GPS Lock
**Entity:** `binary_sensor.web_888_gps_lock`
**Type:** Binary
**Description:** Whether the GPS has acquired a fix.

### GPS Fixes
**Entity:** `sensor.web_888_gps_fixes`
**Unit:** fixes
**Description:** Number of GPS fixes received since boot.

### GPS Fixes/min
**Entity:** `sensor.web_888_gps_fixes_per_min`
**Unit:** fixes/min
**Description:** GPS position fixes per minute.

### GPS Fixes/hour
**Entity:** `sensor.web_888_gps_fixes_per_hour`
**Unit:** fixes/hour
**Description:** GPS position fixes per hour.

### GPS Good Satellites
**Entity:** `sensor.web_888_gps_good`
**Unit:** satellites
**Description:** Number of satellites with good signal quality.

### GPS Satellites (WebSocket only)
**Entity:** `sensor.web_888_gps_satellites`
**Unit:** satellites
**Description:** Total visible satellites.

### GPS Tracking (WebSocket only)
**Entity:** `sensor.web_888_gps_tracking`
**Unit:** satellites
**Description:** Number of satellites currently being tracked.

### GPS In Solution (WebSocket only)
**Entity:** `sensor.web_888_gps_in_solution`
**Unit:** satellites
**Description:** Number of satellites used in position fix.

### GPS Avg SNR (WebSocket only)
**Entity:** `sensor.web_888_gps_avg_snr`
**Unit:** dB
**Description:** Average signal-to-noise ratio across tracked satellites.

### GPS Acquiring (WebSocket only)
**Entity:** `binary_sensor.web_888_gps_acquiring`
**Type:** Binary
**Description:** Whether GPS is actively acquiring satellites.

### Grid Square (WebSocket only)
**Entity:** `sensor.web_888_grid_square`
**Description:** Maidenhead grid locator (e.g., EM13lb).

### Latitude / Longitude
**Entity:** `sensor.web_888_latitude`, `sensor.web_888_longitude`
**Unit:** degrees
**Category:** Diagnostic
**Description:** GPS coordinates.

### Altitude
**Entity:** `sensor.web_888_altitude`
**Unit:** meters
**Category:** Diagnostic
**Description:** GPS altitude above sea level.

### ADC Clock (WebSocket only)
**Entity:** `sensor.web_888_adc_clock`
**Unit:** MHz
**Category:** Diagnostic
**Description:** ADC reference clock frequency.

### Frequency Offset
**Entity:** `sensor.web_888_freq_offset`
**Unit:** Hz
**Category:** Diagnostic
**Description:** Calibration frequency offset.

---

## Signal Quality Sensors

### SNR All Bands
**Entity:** `sensor.web_888_snr_all_bands`
**Unit:** dB
**Device Class:** signal_strength
**Description:** Signal-to-noise ratio across all bands (0-30 MHz).

### SNR HF
**Entity:** `sensor.web_888_snr_hf`
**Unit:** dB
**Device Class:** signal_strength
**Description:** Signal-to-noise ratio for HF bands (3-30 MHz).

---

## System Health Sensors

### CPU Temperature (WebSocket only)
**Entity:** `sensor.web_888_cpu_temperature`
**Unit:** °C
**Device Class:** temperature
**Category:** Diagnostic
**Description:** ZYNQ processor temperature.

### CPU Frequency (WebSocket only)
**Entity:** `sensor.web_888_cpu_freq`
**Unit:** MHz
**Category:** Diagnostic
**Description:** Processor clock speed.

### CPU Usage (WebSocket only)
**Entity:** `sensor.web_888_cpu_usage`
**Unit:** %
**Category:** Diagnostic
**Description:** Average CPU utilization.

### Thermal Warning (WebSocket only)
**Entity:** `binary_sensor.web_888_thermal_warning`
**Type:** Binary
**Description:** Triggers when CPU exceeds configured threshold (default 70°C).

### Antenna Connected
**Entity:** `binary_sensor.web_888_antenna_connected`
**Type:** Binary
**Device Class:** plug
**Description:** Whether an antenna is detected.

### ADC Overflow
**Entity:** `sensor.web_888_adc_overflow`
**Unit:** overflows
**Category:** Diagnostic
**Description:** Number of ADC overflow events (signal clipping).

---

## Bandwidth Sensors (WebSocket only)

### Audio Bandwidth
**Entity:** `sensor.web_888_audio_bandwidth`
**Unit:** B/s
**Device Class:** data_rate
**Category:** Diagnostic
**Description:** Audio streaming bandwidth.

### Waterfall Bandwidth
**Entity:** `sensor.web_888_waterfall_bandwidth`
**Unit:** B/s
**Device Class:** data_rate
**Category:** Diagnostic
**Description:** Waterfall data rate.

### HTTP Bandwidth
**Entity:** `sensor.web_888_http_bandwidth`
**Unit:** B/s
**Device Class:** data_rate
**Category:** Diagnostic
**Description:** HTTP traffic rate.

---

## Diagnostic Counters (WebSocket only)

### Audio Dropped
**Entity:** `sensor.web_888_audio_dropped`
**Unit:** packets
**Category:** Diagnostic
**Description:** Dropped audio packet count.

### Audio Underruns
**Entity:** `sensor.web_888_audio_underruns`
**Unit:** events
**Category:** Diagnostic
**Description:** Audio buffer underrun events.

### Sequence Errors (v1.2.1)
**Entity:** `sensor.web_888_sequence_errors`
**Unit:** errors
**Category:** Diagnostic
**Description:** Sequence error counter from device stats.

### Realtime Errors (v1.2.1)
**Entity:** `sensor.web_888_realtime_errors`
**Unit:** errors
**Category:** Diagnostic
**Description:** Realtime error counter from device stats.

---

## Decode Sensors (WebSocket only)

### Total Decodes
**Entity:** `sensor.web_888_total_decodes`
**Unit:** decodes
**Description:** Sum of all decoded messages across all channels.

### FT8 Total Decodes
**Entity:** `sensor.web_888_ft8_total_decodes`
**Unit:** decodes
**Description:** Total FT8 decodes across all FT8 channels.

### WSPR Total Decodes
**Entity:** `sensor.web_888_wspr_total_decodes`
**Unit:** decodes
**Description:** Total WSPR decodes across all WSPR channels.

---

## Channel Type Sensors (WebSocket only)

### FT8 Channels
**Entity:** `sensor.web_888_ft8_channels`
**Unit:** channels
**Description:** Count of channels running FT8 extension.

### WSPR Channels
**Entity:** `sensor.web_888_wspr_channels`
**Unit:** channels
**Description:** Count of channels running WSPR extension.

### User Channels
**Entity:** `sensor.web_888_user_channels`
**Unit:** channels
**Description:** Count of channels with real users connected.

### Idle Channels
**Entity:** `sensor.web_888_idle_channels`
**Unit:** channels
**Description:** Count of unused channels.

### Preemptible Channels (v1.2.1)
**Entity:** `sensor.web_888_preemptible_channels`
**Unit:** channels
**Description:** Count of channels that can be preempted by users.

### Total Session Hours (v1.2.1)
**Entity:** `sensor.web_888_total_session_hours`
**Unit:** hours
**Category:** Diagnostic
**Description:** Combined runtime of all active channels.

---

## Per-Channel Sensors (WebSocket only)

Per-channel sensors are created when "Enable Per-Channel Sensors" is enabled. Each of the 12 RX channels has three sensors:

### Channel N Frequency
**Entity:** `sensor.web_888_channel_N_frequency`
**Unit:** Hz
**Device Class:** frequency
**Description:** Currently tuned frequency for channel N.

**Extra attributes:**
- `frequency_khz` - Frequency in kHz
- `frequency_mhz` - Frequency in MHz
- `channel_name` - User-defined channel name (e.g., "FT8-20m")
- `active` - Whether channel is in use
- `channel_type` - Type: ft8, wspr, user, idle
- `extension` - Extension name (FT8, wspr, etc.)
- `is_extension` - Whether running an extension
- `client_ip` - Client IP (127.0.0.1 for autorun)
- `session_time` - Runtime in HH:MM:SS format (v1.2.1)
- `session_seconds` - Runtime in seconds (v1.2.1)
- `preemptible` - Whether can be preempted (v1.2.1)

### Channel N Mode
**Entity:** `sensor.web_888_channel_N_mode`
**Description:** Demodulation mode (USB, LSB, AM, CW, Idle).

### Channel N Decoded
**Entity:** `sensor.web_888_channel_N_decoded`
**Unit:** decodes
**Description:** Number of decoded messages on channel N.

---

## Reporter Config Sensors (WebSocket only)

Auto-discovered from device configuration.

### Reporter Callsign
**Entity:** `sensor.web_888_reporter_callsign`
**Description:** Effective callsign for reporting (FT8 if set, else WSPR).

### Reporter Grid
**Entity:** `sensor.web_888_reporter_grid`
**Description:** Effective grid square for reporting.

### WSPR Callsign / Grid
**Entity:** `sensor.web_888_wspr_callsign`, `sensor.web_888_wspr_grid`
**Description:** Callsign and grid for wsprnet.org reporting.

### FT8 Callsign / Grid
**Entity:** `sensor.web_888_ft8_callsign`, `sensor.web_888_ft8_grid`
**Description:** Callsign and grid for PSKReporter (often falls back to WSPR).

### Reporter SNR Correction
**Entity:** `sensor.web_888_reporter_snr_correction`
**Unit:** dB
**Category:** Diagnostic
**Description:** SNR adjustment applied before reporting.

### Reporter dT Correction
**Entity:** `sensor.web_888_reporter_dt_correction`
**Unit:** seconds
**Category:** Diagnostic
**Description:** Time adjustment applied before reporting.

### WSPR Autorun Channels
**Entity:** `sensor.web_888_wspr_autorun_channels`
**Unit:** channels
**Category:** Diagnostic
**Description:** Number of configured WSPR autorun slots.

### FT8 Autorun Channels
**Entity:** `sensor.web_888_ft8_autorun_channels`
**Unit:** channels
**Category:** Diagnostic
**Description:** Number of configured FT8 autorun slots.

---

## Device Config Sensors (WebSocket only, v1.2.0+)

Exposed from device admin configuration.

### Calibration
- **S-Meter Calibration** (`sensor.web_888_cfg_s_meter_cal`) - S-meter offset (dB)
- **Waterfall Calibration** (`sensor.web_888_cfg_waterfall_cal`) - Waterfall offset (dB)
- **Overload Mute** (`sensor.web_888_cfg_overload_mute`) - Overload mute threshold (dB)
- **Clock Adjustment** (`sensor.web_888_cfg_clk_adj`) - Clock trim value

### Session Config
- **Inactivity Timeout** (`sensor.web_888_cfg_inactivity_timeout`) - Auto-disconnect timeout (minutes)
- **Password-Free Channels** (`sensor.web_888_cfg_chan_no_pwd`) - Channels without password
- **Camping Slots** (`sensor.web_888_cfg_camping_slots`) - Number of camping slots
- **API Channels** (`sensor.web_888_cfg_api_channels`) - Channels for external API

### Network Config
- **Configured IP** (`sensor.web_888_cfg_static_ip`) - Static IP if configured
- **Service Port** (`sensor.web_888_cfg_port`) - Web service port

### Device Info
- **Device Name** (`sensor.web_888_cfg_rx_name`) - Configured receiver name
- **Antenna Description** (`sensor.web_888_cfg_rx_antenna`) - Antenna info
- **Altitude ASL** (`sensor.web_888_cfg_rx_asl`) - Altitude above sea level (m)
- **Owner Email** (`sensor.web_888_cfg_owner_email`) - Owner contact

---

## Feature Flag Binary Sensors (WebSocket only, v1.2.0+)

All have `EntityCategory.DIAGNOSTIC`:

- **GPS Enabled** (`binary_sensor.web_888_cfg_gps_enabled`)
- **GPS Correction** (`binary_sensor.web_888_cfg_gps_correction`)
- **DRM Enabled** (`binary_sensor.web_888_cfg_drm_enabled`)
- **WSPR Enabled** (`binary_sensor.web_888_cfg_wspr_enabled`)
- **WSPR Spot Logging** (`binary_sensor.web_888_cfg_wspr_spot_log`)
- **WSPR Auto-Update Grid** (`binary_sensor.web_888_cfg_wspr_gps_grid`)
- **Server Enabled** (`binary_sensor.web_888_cfg_server_enabled`)
- **Airband Mode** (`binary_sensor.web_888_cfg_airband`)
- **Static IP Mode** (`binary_sensor.web_888_cfg_use_static_ip`)
- **SDR.hu Listed** (`binary_sensor.web_888_cfg_sdr_hu_listed`)
- **KiwiSDR.com Listed** (`binary_sensor.web_888_cfg_kiwisdr_listed`)

---

## Per-Satellite Sensors (WebSocket only, Optional)

Enabled via "Enable Satellite Sensors" option. Creates 5 sensors per tracked satellite (up to 12 satellites = 60 sensors).

### Satellite N SNR
**Entity:** `sensor.web_888_satellite_N_snr`
**Unit:** dB
**Description:** Signal-to-noise ratio for satellite N.

**Extra attributes:**
- `system` - Satellite system (GPS, GLONASS, BeiDou)
- `prn` - PRN number
- `azimuth` - Azimuth angle (degrees)
- `elevation` - Elevation angle (degrees)
- `in_solution` - Whether used in position fix
- `tracked` - Whether actively tracked (v1.2.1)

---

## Sensor Counts by Version

| Version | Device Sensors | Binary Sensors | Channel Sensors | Satellite Sensors |
|---------|----------------|----------------|-----------------|-------------------|
| v1.0.0 | ~22 | 4 | 36 | 0 |
| v1.1.0 | ~55 | 6 | 36 | 60 (optional) |
| v1.2.0 | ~70 | 17 | 36 | 60 (optional) |
| v1.2.1 | ~74 | 17 | 36 | 60 (optional) |
