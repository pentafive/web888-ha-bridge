# Home Assistant Dashboard Examples

Example Lovelace configurations for displaying Web-888 HA Bridge data.

## Entity ID Format

Entity IDs vary based on deployment method and device name:

| Deployment | Example Entity ID |
|------------|-------------------|
| HACS | `sensor.web_888_10_1_1_28_users` |
| Docker/MQTT | `sensor.web888_10_1_1_28_users` |

Update the entity IDs in examples below to match your setup.

---

## Basic Status Card

Simple entities card showing key metrics:

```yaml
type: entities
title: Web-888 SDR Status
entities:
  - entity: binary_sensor.web_888_connected
    name: Connection
  - entity: sensor.web_888_users
    name: Active Users
  - entity: sensor.web_888_snr_all_bands
    name: SNR (All Bands)
  - entity: sensor.web_888_gps_fixes
    name: GPS Fixes
  - entity: sensor.web_888_uptime
    name: Uptime
```

## GPS Status Card

Monitor GPS health and position:

```yaml
type: entities
title: Web-888 GPS
entities:
  - entity: binary_sensor.web_888_gps_lock
    name: GPS Lock
  - entity: sensor.web_888_gps_good
    name: Good Satellites
  - entity: sensor.web_888_grid_square
    name: Grid Square
  - entity: sensor.web_888_latitude
    name: Latitude
  - entity: sensor.web_888_longitude
    name: Longitude
  - entity: sensor.web_888_altitude
    name: Altitude
```

## System Health Card

Monitor device health:

```yaml
type: entities
title: Web-888 System
entities:
  - entity: sensor.web_888_cpu_temperature
    name: CPU Temperature
  - entity: sensor.web_888_uptime
    name: Uptime
  - entity: sensor.web_888_adc_overflow
    name: ADC Overflows
  - entity: binary_sensor.web_888_antenna_connected
    name: Antenna
  - entity: sensor.web_888_device_status
    name: Status
```

## Glance Card

Compact overview for smaller dashboards:

```yaml
type: glance
title: Web-888 SDR
entities:
  - entity: binary_sensor.web_888_connected
    name: Online
  - entity: sensor.web_888_users
    name: Users
  - entity: sensor.web_888_snr_hf
    name: SNR HF
  - entity: binary_sensor.web_888_gps_lock
    name: GPS
```

## Tile Cards with Color Thresholds

Requires [card-mod](https://github.com/thomasloven/lovelace-card-mod) from HACS:

```yaml
type: grid
columns: 3
cards:
  - type: tile
    entity: sensor.web_888_snr_all_bands
    name: SNR
    icon: mdi:signal
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(0) %}
          {% if val < 10 %} --tile-color: #db4437;
          {% elif val < 20 %} --tile-color: #ffa600;
          {% endif %}
        }
  - type: tile
    entity: sensor.web_888_cpu_temperature
    name: CPU Temp
    icon: mdi:thermometer
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(0) %}
          {% if val > 70 %} --tile-color: #db4437;
          {% elif val > 60 %} --tile-color: #ffa600;
          {% endif %}
        }
  - type: tile
    entity: sensor.web_888_users
    name: Users
    icon: mdi:account-multiple
    color: blue
```

## Channel Activity Card (WebSocket Mode)

Monitor active decoder channels:

```yaml
type: entities
title: FT8 Channels
entities:
  - entity: sensor.web_888_channel_1_frequency
    name: Channel 1
    secondary_info: last-changed
  - entity: sensor.web_888_channel_1_mode
  - entity: sensor.web_888_channel_1_decoded
    name: Decodes
  - type: divider
  - entity: sensor.web_888_channel_2_frequency
    name: Channel 2
  - entity: sensor.web_888_channel_2_mode
  - entity: sensor.web_888_channel_2_decoded
    name: Decodes
```

## History Graph

Track SNR and users over time:

```yaml
type: history-graph
title: Web-888 Performance
hours_to_show: 24
entities:
  - entity: sensor.web_888_snr_all_bands
    name: SNR All
  - entity: sensor.web_888_snr_hf
    name: SNR HF
  - entity: sensor.web_888_users
    name: Users
```

## Temperature History

Track thermal performance:

```yaml
type: history-graph
title: Web-888 Temperature
hours_to_show: 24
entities:
  - entity: sensor.web_888_cpu_temperature
    name: CPU
```

## Multi-Device Dashboard

If monitoring multiple Web-888 receivers:

```yaml
type: grid
columns: 2
cards:
  - type: entities
    title: FT8 Receiver
    entities:
      - entity: binary_sensor.web_888_10_1_1_28_connected
      - entity: sensor.web_888_10_1_1_28_users
      - entity: sensor.web_888_10_1_1_28_total_decodes
  - type: entities
    title: WSPR Receiver
    entities:
      - entity: binary_sensor.web_888_10_1_1_29_connected
      - entity: sensor.web_888_10_1_1_29_users
      - entity: sensor.web_888_10_1_1_29_total_decodes
```

---

## Useful Automations

### Alert on Disconnection

```yaml
alias: "Alert: Web-888 Offline"
trigger:
  - platform: state
    entity_id: binary_sensor.web_888_connected
    to: "off"
    for:
      minutes: 5
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 Disconnected"
      message: "SDR receiver has been offline for 5 minutes"
```

### Alert on GPS Lock Lost

```yaml
alias: "Alert: Web-888 GPS Lost"
trigger:
  - platform: state
    entity_id: binary_sensor.web_888_gps_lock
    to: "off"
    for:
      minutes: 10
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 GPS Warning"
      message: "GPS lock lost on SDR receiver"
```

### Alert on High CPU Temperature

```yaml
alias: "Alert: Web-888 Overheating"
trigger:
  - platform: numeric_state
    entity_id: sensor.web_888_cpu_temperature
    above: 70
    for:
      minutes: 5
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 Temperature Warning"
      message: "CPU temperature is {{ states('sensor.web_888_cpu_temperature') }}°C"
```

### Track Daily Decodes

```yaml
alias: "Log Daily Decodes"
trigger:
  - platform: time
    at: "23:59:00"
action:
  - service: logbook.log
    data:
      name: Web-888
      message: "Daily decodes: {{ states('sensor.web_888_total_decodes') }}"
```

---

## Pre-built Dashboards

Full dashboard YAML files are available in the repository:

- [`examples/entities-card.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/entities-card.yaml) - Basic entities card
- [`examples/glance-card.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/glance-card.yaml) - Compact glance view
- [`examples/history-graph.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/history-graph.yaml) - Historical charts

---

## Contributing

Share your dashboard configs! Open a PR or submit an issue with your setup.
