<p align="center">
  <img src="images/logo.png" alt="Web-888 HA Bridge" width="600">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/pentafive/web888-ha-bridge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pentafive/web888-ha-bridge" alt="License"></a>
  <a href="https://buymeacoffee.com/pentafive"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?logo=buymeacoffee" alt="Buy Me a Coffee"></a>
</p>

Monitor your [Web-888 SDR](https://www.rx-888.com/web/) software-defined radio receiver in Home Assistant. Track users, GPS status, signal-to-noise ratio, channel activity, and more with real-time dashboard integration.

## Features

- **Real-time SDR Monitoring** - Connected users, uptime, CPU temperature
- **GPS Tracking** - Lock status, satellites, grid square, coordinates
- **Signal Quality** - SNR measurements for all bands and HF
- **Channel Activity** - Frequency, mode, and decode counts per channel (WebSocket mode)
- **System Health** - ADC overflow, antenna status, device status
- **Two Deployment Options** - Native HACS integration or Docker/MQTT bridge

## Supported Hardware

This integration works with **Web-888 SDR** receivers from the RX-888 project:

- Web-888 (Xilinx ZYNQ XC7Z010)
- Other KiwiSDR-compatible devices (basic HTTP mode support)

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/pentafive/web888-ha-bridge` as an **Integration**
4. Search for "Web-888 SDR Monitor" and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for "Web-888 SDR Monitor" and configure

### Option 2: Docker/MQTT Bridge

For users who prefer container deployment or need MQTT-based integration:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/pentafive/web888-ha-bridge.git
    cd web888-ha-bridge
    ```

2. **Configure:** Copy `.env.example` to `.env` and edit:
    ```bash
    cp .env.example .env
    nano .env
    ```

3. **Run with Docker Compose:**
    ```bash
    docker compose up -d
    ```

## Sensors

| Category | Sensors |
|----------|---------|
| **Users** | Connected Users, Users Max |
| **System** | Uptime, CPU Temperature*, ADC Overflow Count |
| **GPS** | GPS Lock, GPS Fixes, GPS Good Satellites, Grid Square*, Latitude, Longitude, Altitude |
| **Signal** | SNR All Bands, SNR HF |
| **Status** | Connected, Antenna Connected, Offline, Device Status, Frequency Bands |
| **Channels*** | Frequency, Mode, Decoded Count (×12 channels) |

*\* WebSocket mode only (requires admin password)*

### Connection Modes

| Mode | Authentication | Data Available |
|------|----------------|----------------|
| **HTTP** | None required | Basic status, GPS, SNR, users |
| **WebSocket** | Admin password | Full data including CPU temp, channels, grid square |

## Configuration

### HACS Integration

Configure via the UI - no YAML required:

| Option | Description | Default |
|--------|-------------|---------|
| Host | IP address of your Web-888 | Required |
| Port | WebSocket port | 8073 |
| Password | Admin password (enables WebSocket mode) | Optional |
| MAC Address | For HA device registry linking | Optional |
| Scan Interval | Update frequency (seconds) | 30 |
| Enable Channels | Create per-channel sensors | False |

### Docker Bridge

All configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WEB888_HOST` | Web-888 IP address | Required |
| `WEB888_PORT` | WebSocket port | 8073 |
| `WEB888_PASSWORD` | Admin password | Optional |
| `WEB888_MAC` | MAC address for device linking | Optional |
| `HA_MQTT_BROKER` | MQTT broker host | Required |
| `HA_MQTT_PORT` | MQTT broker port | 1883 |
| `SCAN_INTERVAL` | Update frequency (seconds) | 30 |

See `.env.example` for all configuration options.

## Documentation

📚 **[Full Documentation Wiki](https://github.com/pentafive/web888-ha-bridge/wiki)**

- [Home](https://github.com/pentafive/web888-ha-bridge/wiki/Home) - Overview and quick start
- [Sensor Reference](https://github.com/pentafive/web888-ha-bridge/wiki/Sensor-Reference) - Understanding each metric
- [Dashboard Examples](https://github.com/pentafive/web888-ha-bridge/wiki/Dashboard-Examples) - Lovelace configs
- [Troubleshooting](https://github.com/pentafive/web888-ha-bridge/wiki/Troubleshooting) - Common issues and solutions

## Dashboard Examples

### Entities Card

```yaml
type: entities
title: Web-888 SDR
entities:
  - entity: binary_sensor.web_888_connected
  - entity: sensor.web_888_users
  - entity: sensor.web_888_snr_all_bands
  - entity: sensor.web_888_gps_fixes
  - entity: sensor.web_888_uptime
```

See `examples/` directory for more dashboard configurations.

## Requirements

- **Web-888 SDR** with network connectivity
- **Home Assistant** 2024.1.0 or newer (for HACS)

### For Docker Bridge Only

- **MQTT Broker** (e.g., Mosquitto)
- **MQTT Integration** in Home Assistant with discovery enabled

## Technical Details

### Protocol

The integration supports two connection modes:

- **HTTP Mode:** Polls `http://<host>:<port>/status` for basic data
- **WebSocket Mode:** Connects to `ws://<host>:<port>/kiwi/<ts>/admin` for full real-time data

### Data Sources

| Mode | Endpoint | Data |
|------|----------|------|
| HTTP | `/status` | Users, GPS, SNR, uptime, device info |
| WebSocket | Admin channel | CPU temp, channels, grid square, audio stats |

## Related Projects

If you're using your Web-888 for FT8/WSPR spotting, check out:

- **[pskr-ha-bridge](https://github.com/pentafive/pskr-ha-bridge)** - Monitor PSKReporter spots in Home Assistant. Track your station's FT8/WSPR/CW activity, spots per band, DX records, and more.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full release history.

| Version | Type | Description |
|---------|------|-------------|
| 1.2.2 | HACS | WebSocket log noise reduction, exponential reconnect backoff |
| 1.2.1 | HACS | Entity category fix, connection stability improvements |
| 1.2.0 | HACS | Full device config exposure, feature flag sensors |
| 1.1.0 | Both | Hybrid mode, thermal monitoring, satellite sensors |
| 1.0.0 | Both | Initial release with HTTP and WebSocket support |

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Support

If you find this integration useful, consider supporting development:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?logo=buymeacoffee)](https://buymeacoffee.com/pentafive)

## Acknowledgements

- **[RX-888 Team](https://www.rx-888.com/)** - Web-888 SDR hardware
- **[KiwiSDR Project](https://github.com/jks-prv/kiwiclient)** - WebSocket protocol reference
- **[RaspSDR/server](https://github.com/RaspSDR/server)** - Server implementation reference
- **[Home Assistant](https://www.home-assistant.io/)** - Home automation platform

## Resources

- [Web-888 Product Page](https://www.rx-888.com/web/)
- [RaspSDR Server (Web-888 firmware)](https://github.com/RaspSDR/server)
- [KiwiClient Python Library](https://github.com/jks-prv/kiwiclient)
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
