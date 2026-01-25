<p align="center">
  <img src="images/logo.png" alt="Web-888 HA Bridge" width="600">
</p>

<p align="center">
  <a href="https://github.com/pentafive/web888-ha-bridge/actions/workflows/hacs-validation.yml"><img src="https://github.com/pentafive/web888-ha-bridge/actions/workflows/hacs-validation.yml/badge.svg" alt="HACS Validation"></a>
  <a href="https://github.com/pentafive/web888-ha-bridge/actions/workflows/ruff.yml"><img src="https://github.com/pentafive/web888-ha-bridge/actions/workflows/ruff.yml/badge.svg" alt="Ruff"></a>
</p>

Monitor your [Web-888 SDR](https://www.rx-888.com/web/) software defined radio receiver in Home Assistant.

Track signal strength, channel activity, FT8/WSPR spots, GPS status, and more with real-time dashboard integration.

## Features

- **Real-time SDR Monitoring** - Signal strength (RSSI), frequency, mode per channel
- **Spot Tracking** - FT8, WSPR, and CW decoder spots with statistics
- **GPS Status** - Lock state, satellite count, position
- **System Health** - CPU temperature, memory, connected users
- **Two Deployment Options** - Native HACS integration or Docker/MQTT bridge

## Supported Hardware

This integration works with **Web-888 SDR** receivers from the RX-888 project:

- Web-888 (Xilinx ZYNQ XC7Z010)
- Other KiwiSDR-compatible devices (basic support)

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

### Device Sensors

| Sensor | Description |
|--------|-------------|
| Connection Status | WebSocket connection state |
| Uptime | Device uptime |
| CPU Temperature | Processor temperature |
| Memory Usage | RAM utilization |
| Connected Users | Active web interface users |
| Active Channels | RX channels in use |

### GPS Sensors

| Sensor | Description |
|--------|-------------|
| GPS Lock | Has satellite fix |
| Satellites | Visible satellite count |
| Latitude | GPS latitude |
| Longitude | GPS longitude |

### Channel Sensors (per channel)

| Sensor | Description |
|--------|-------------|
| Frequency | Tuned frequency (Hz) |
| Mode | Demodulation mode (AM/USB/LSB/CW/FM) |
| RSSI | Signal strength (dBm) |
| SNR | Signal-to-noise ratio (dB) |
| Active | Channel in use |

### Skimmer Sensors

| Sensor | Description |
|--------|-------------|
| FT8 Spots Total | Total FT8 spots decoded |
| FT8 Spots/Hour | Recent FT8 activity rate |
| FT8 Last Callsign | Most recent spotted call |
| FT8 Max Distance | Furthest FT8 spot (km) |
| WSPR Spots Total | Total WSPR spots |
| WSPR Spots/Hour | Recent WSPR activity |

## Configuration

### HACS Integration

Configure via the UI - no YAML required:

| Option | Description | Default |
|--------|-------------|---------|
| Host | IP address of your Web-888 | Required |
| Port | WebSocket port | 8073 |
| Scan Interval | Update frequency (seconds) | 30 |
| Enable Skimmer | Monitor FT8/WSPR spots | True |

### Docker Bridge

All configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WEB888_HOST` | Web-888 IP address | Required |
| `WEB888_PORT` | WebSocket port | 8073 |
| `HA_MQTT_BROKER` | MQTT broker host | Required |
| `HA_MQTT_PORT` | MQTT broker port | 1883 |
| `SCAN_INTERVAL` | Update frequency (seconds) | 30 |

See `.env.example` for all configuration options.

## Dashboard Examples

### Entities Card

```yaml
type: entities
title: Web-888 SDR
entities:
  - entity: binary_sensor.web888_connection_status
  - entity: sensor.web888_active_channels
  - entity: sensor.web888_ft8_spots_hour
  - entity: sensor.web888_cpu_temperature
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

The bridge connects to the Web-888 using the KiwiSDR WebSocket protocol:

- **WebSocket:** `ws://<host>:8073/<session>/SND`
- **Status:** `http://<host>:8073/status`

### Data Sources

1. **WebSocket Stream** - Real-time audio/RSSI data
2. **Status API** - Device info, GPS, users
3. **Spot Feed** - Decoded FT8/WSPR/CW spots

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Acknowledgements

- **[RX-888 Team](https://www.rx-888.com/)** - Web-888 SDR hardware
- **[KiwiSDR Project](https://github.com/jks-prv/kiwiclient)** - WebSocket protocol
- **[Home Assistant](https://www.home-assistant.io/)** - Home automation platform

## Resources

- [Web-888 Product Page](https://www.rx-888.com/web/)
- [KiwiClient Python Library](https://github.com/jks-prv/kiwiclient)
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
