# Sensor Reference

Detailed documentation for all sensors provided by Web-888 HA Bridge.

## Availability by Mode

| Sensor | HTTP Mode | WebSocket Mode |
|--------|-----------|----------------|
| Users | Yes | Yes |
| Users Max | Yes | Yes |
| Uptime | Yes | Yes |
| GPS Fixes | Yes | Yes |
| GPS Good Satellites | Yes | Yes |
| GPS Lock | Yes | Yes |
| Latitude/Longitude | Yes | Yes |
| Altitude | Yes | Yes |
| SNR All Bands | Yes | Yes |
| SNR HF | Yes | Yes |
| Device Status | Yes | Yes |
| Frequency Bands | Yes | Yes |
| Antenna Connected | Yes | Yes |
| Offline | Yes | Yes |
| ADC Overflow | Yes | Yes |
| CPU Temperature | No | Yes |
| Grid Square | No | Yes |
| GPS Satellites (total) | No | Yes |
| Total Decodes | No | Yes |
| Audio Bandwidth | No | Yes |
| Channel Sensors | No | Yes |

---

## User Sensors

### Users
**Entity:** `sensor.web_888_users`
**Unit:** users
**Description:** Number of currently connected users listening to the Web-888.

**What to expect:**
- 0 = No active listeners
- Public receivers typically show 1-12+ users
- Private receivers show fewer connections

### Users Max
**Entity:** `sensor.web_888_users_max`
**Unit:** users
**Category:** Diagnostic
**Description:** Maximum simultaneous users allowed.

**What to expect:**
- Typically 12 for standard Web-888 configuration
- 0 may indicate private/restricted mode

---

## GPS Sensors

### GPS Lock
**Entity:** `binary_sensor.web_888_gps_lock`
**Type:** Binary (Connected/Disconnected)
**Description:** Whether the GPS has acquired a fix.

**What to expect:**
- Connected = GPS has valid fix
- Disconnected = No GPS fix (indoor, no antenna, or starting up)

### GPS Fixes
**Entity:** `sensor.web_888_gps_fixes`
**Unit:** fixes
**Description:** Number of GPS fixes received since boot.

**What to expect:**
- Increases over time with valid GPS signal
- Higher numbers indicate stable GPS reception

### GPS Good Satellites
**Entity:** `sensor.web_888_gps_good`
**Unit:** satellites
**Description:** Number of satellites with good signal quality.

**What to expect:**
- 0 = No GPS reception
- 4+ = Minimum for position fix
- 8-12+ = Excellent reception

### GPS Satellites (WebSocket only)
**Entity:** `sensor.web_888_gps_satellites`
**Unit:** satellites
**Description:** Total visible satellites (including weak signals).

### Grid Square (WebSocket only)
**Entity:** `sensor.web_888_grid_square`
**Description:** Maidenhead grid locator calculated from GPS position.

**What to expect:**
- 6-character grid (e.g., EM13lb)
- Used by amateur radio for location reference
- Empty if no GPS fix

### Latitude / Longitude
**Entity:** `sensor.web_888_latitude`, `sensor.web_888_longitude`
**Unit:** degrees
**Category:** Diagnostic
**Description:** GPS coordinates.

**What to expect:**
- Valid coordinates when GPS has fix
- May show 0 or Unknown without GPS lock

### Altitude
**Entity:** `sensor.web_888_altitude`
**Unit:** meters (displayed as feet in some configs)
**Category:** Diagnostic
**Description:** GPS altitude above sea level.

---

## Signal Quality Sensors

### SNR All Bands
**Entity:** `sensor.web_888_snr_all_bands`
**Unit:** dB
**Device Class:** signal_strength
**Description:** Signal-to-noise ratio across all bands (0-30 MHz).

**What to expect:**
- 0 or Unknown = SNR measurement disabled or not yet performed
- 10-15 dB = Moderate noise environment
- 20-30 dB = Good/quiet location
- 30+ dB = Excellent RF environment

**Note:** SNR measurement requires:
1. A free channel slot on the device
2. SNR measurement enabled in admin settings
3. Measurement interval (hourly by default, or manual "Measure SNR now")

### SNR HF
**Entity:** `sensor.web_888_snr_hf`
**Unit:** dB
**Device Class:** signal_strength
**Description:** Signal-to-noise ratio for HF bands only (3-30 MHz).

**What to expect:**
- Similar to SNR All Bands but focused on amateur/shortwave frequencies
- Often 1-2 dB different from All Bands measurement

---

## System Health Sensors

### Uptime
**Entity:** `sensor.web_888_uptime`
**Unit:** seconds
**Device Class:** duration
**Category:** Diagnostic
**Description:** Time since device boot.

### CPU Temperature (WebSocket only)
**Entity:** `sensor.web_888_cpu_temperature`
**Unit:** °C (displayed as °F in some configs)
**Device Class:** temperature
**Category:** Diagnostic
**Description:** ZYNQ processor temperature.

**What to expect:**
- 40-60°C = Normal operation
- 60-70°C = Warm but acceptable
- 70°C+ = Consider improving ventilation

### ADC Overflow Count
**Entity:** `sensor.web_888_adc_overflow`
**Unit:** overflows
**Category:** Diagnostic
**Description:** Number of ADC overflow events (signal clipping).

**What to expect:**
- 0 = Normal operation
- Increasing = Strong local signal causing overload
- Consider adding attenuation if frequently increasing

### Audio Bandwidth (WebSocket only)
**Entity:** `sensor.web_888_audio_bandwidth`
**Unit:** Hz
**Category:** Diagnostic
**Description:** Current audio streaming bandwidth.

---

## Status Sensors

### Connected
**Entity:** `binary_sensor.web_888_connected`
**Type:** Binary
**Device Class:** connectivity
**Description:** Integration connection to the Web-888.

### Device Status
**Entity:** `sensor.web_888_device_status`
**Category:** Diagnostic
**Description:** Current device operating mode.

**Values:**
- `active` = Normal operation, accepting connections
- `private` = Restricted access mode
- `offline` = Device not responding

### Antenna Connected
**Entity:** `binary_sensor.web_888_antenna_connected`
**Type:** Binary
**Device Class:** plug
**Description:** Whether an antenna is detected.

**What to expect:**
- Plugged in = Antenna connected
- Unplugged = No antenna or antenna issue detected

### Offline
**Entity:** `binary_sensor.web_888_offline`
**Type:** Binary
**Device Class:** problem
**Description:** Device offline status.

**What to expect:**
- OK = Device responding normally
- Problem = Device not responding

### Frequency Bands
**Entity:** `sensor.web_888_frequency_bands`
**Category:** Diagnostic
**Description:** Configured frequency range.

**What to expect:**
- Typically `0-30000000` (0-30 MHz) for standard Web-888

---

## Channel Sensors (WebSocket only)

Per-channel sensors are created when "Enable Per-Channel Sensors" is enabled. Each of the 12 RX channels has three sensors:

### Channel N Frequency
**Entity:** `sensor.web_888_channel_N_frequency`
**Unit:** Hz
**Device Class:** frequency
**Description:** Currently tuned frequency for channel N.

**Extra attributes:**
- `frequency_khz` - Frequency in kHz
- `frequency_mhz` - Frequency in MHz
- `channel_name` - User-defined channel name
- `active` - Whether channel is in use

### Channel N Mode
**Entity:** `sensor.web_888_channel_N_mode`
**Description:** Demodulation mode for channel N.

**Values:**
- `USB` - Upper sideband
- `LSB` - Lower sideband
- `AM` - Amplitude modulation
- `CW` - Continuous wave
- `Idle` - Channel not in use

### Channel N Decoded
**Entity:** `sensor.web_888_channel_N_decoded`
**Unit:** decodes
**Description:** Number of decoded messages on channel N.

**What to expect:**
- Counts FT8, WSPR, or other digital mode decodes
- Increases over time when decoder is active
- Reset on device reboot

---

## Total Decodes (WebSocket only)

**Entity:** `sensor.web_888_total_decodes`
**Unit:** decodes
**Description:** Sum of all decoded messages across all channels.

**What to expect:**
- Active FT8 station: hundreds to thousands per day
- WSPR: lower numbers due to longer transmission time
