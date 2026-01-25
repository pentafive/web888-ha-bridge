![Web-888 HA Bridge](https://raw.githubusercontent.com/pentafive/web888-ha-bridge/main/images/logo.png)

# Web-888 HA Bridge Wiki

Welcome to the Web-888 HA Bridge wiki - documentation for monitoring your [Web-888 SDR](https://www.rx-888.com/web/) software-defined radio receiver with Home Assistant.

## Quick Links

- [[Sensor-Reference]] - Understanding each metric and what values to expect
- [[Dashboard-Examples]] - Home Assistant dashboard configurations
- [[Troubleshooting]] - Common issues and solutions

## Overview

Web-888 HA Bridge monitors your Web-888 SDR in Home Assistant:

**User Activity:**
- Connected Users and Max Users
- Device Uptime

**GPS Status:**
- GPS Lock and Fix Count
- Good Satellites Count
- Grid Square (WebSocket mode)
- Latitude, Longitude, Altitude

**Signal Quality:**
- SNR All Bands (0-30 MHz)
- SNR HF (3-30 MHz)

**System Health:**
- CPU Temperature (WebSocket mode)
- ADC Overflow Count
- Antenna Connected Status
- Device Status (active/private/offline)

**Channel Activity (WebSocket mode):**
- Per-channel Frequency
- Demodulation Mode
- Decoded Message Count

## Supported Hardware

Works with **Web-888 SDR** receivers:
- Web-888 (Xilinx ZYNQ XC7Z010)
- Other KiwiSDR-compatible devices (HTTP mode only)

## Installation Options

### Option 1: HACS Integration (Recommended)

Native Home Assistant integration with UI configuration:

1. Open HACS → Custom repositories
2. Add `https://github.com/pentafive/web888-ha-bridge` as Integration
3. Install "Web-888 SDR Monitor"
4. Restart Home Assistant
5. Add integration via Settings → Devices & Services

### Option 2: Docker/MQTT Bridge

Container deployment with MQTT auto-discovery:

1. Clone repo and configure `.env`
2. Run `docker compose up -d`
3. Sensors auto-discover in Home Assistant

See [README](https://github.com/pentafive/web888-ha-bridge#readme) for detailed instructions.

## Connection Modes

The integration supports two connection modes:

### HTTP Mode (No Password)

- Polls `/status` endpoint
- Basic sensors: users, GPS, SNR, uptime
- Works with any KiwiSDR-compatible device
- Lower data refresh rate

### WebSocket Mode (With Password)

- Real-time admin channel connection
- Full sensor set including CPU temp, channels, grid square
- Per-channel frequency and decode monitoring
- Requires admin password from Web-888 control panel

**Tip:** If you don't need channel monitoring, HTTP mode is sufficient for most dashboards.

## Related Projects

If you're using your Web-888 for digital mode reception:

- **[pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge)** - Monitor your PSKReporter spots in Home Assistant. Track FT8/WSPR/CW activity, spots per band, DX records, and propagation.

## Getting Started

1. Note your Web-888's IP address (check your router or the device's web interface)
2. (Optional) Get the admin password from the Web-888 control panel for WebSocket mode
3. Choose HACS or Docker deployment
4. Sensors appear automatically in Home Assistant

## Contributing

Found a solution? Have a dashboard config to share? Contributions welcome:

- Dashboard configurations
- Troubleshooting tips
- Documentation improvements

Open an issue or PR on [GitHub](https://github.com/pentafive/web888-ha-bridge).
