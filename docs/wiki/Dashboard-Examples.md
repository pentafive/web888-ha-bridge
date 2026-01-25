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
  - entity: sensor.web_888_gps_tracking
    name: Tracking
  - entity: sensor.web_888_gps_in_solution
    name: In Solution
  - entity: sensor.web_888_gps_avg_snr
    name: Avg SNR
  - entity: sensor.web_888_grid_square
    name: Grid Square
```

## System Health Card

Monitor device health:

```yaml
type: entities
title: Web-888 System
entities:
  - entity: sensor.web_888_cpu_temperature
    name: CPU Temperature
  - entity: sensor.web_888_cpu_freq
    name: CPU Frequency
  - entity: sensor.web_888_cpu_usage
    name: CPU Usage
  - entity: binary_sensor.web_888_thermal_warning
    name: Thermal Warning
  - entity: sensor.web_888_uptime
    name: Uptime
  - entity: binary_sensor.web_888_antenna_connected
    name: Antenna
```

## Bandwidth Monitoring Card

Track network usage:

```yaml
type: entities
title: Web-888 Bandwidth
entities:
  - entity: sensor.web_888_audio_bandwidth
    name: Audio
  - entity: sensor.web_888_waterfall_bandwidth
    name: Waterfall
  - entity: sensor.web_888_http_bandwidth
    name: HTTP
```

## Diagnostic Counters Card (v1.2.1)

Monitor error counters:

```yaml
type: entities
title: Web-888 Diagnostics
entities:
  - entity: sensor.web_888_audio_dropped
    name: Audio Dropped
  - entity: sensor.web_888_audio_underruns
    name: Audio Underruns
  - entity: sensor.web_888_sequence_errors
    name: Sequence Errors
  - entity: sensor.web_888_realtime_errors
    name: Realtime Errors
  - entity: sensor.web_888_adc_overflow
    name: ADC Overflows
```

## FT8/WSPR Monitoring Card

Track digital mode activity:

```yaml
type: entities
title: FT8/WSPR Activity
entities:
  - entity: sensor.web_888_total_decodes
    name: Total Decodes
  - entity: sensor.web_888_ft8_total_decodes
    name: FT8 Decodes
  - entity: sensor.web_888_wspr_total_decodes
    name: WSPR Decodes
  - type: divider
  - entity: sensor.web_888_ft8_channels
    name: FT8 Channels
  - entity: sensor.web_888_wspr_channels
    name: WSPR Channels
  - entity: sensor.web_888_user_channels
    name: User Channels
  - entity: sensor.web_888_idle_channels
    name: Idle Channels
  - type: divider
  - entity: sensor.web_888_preemptible_channels
    name: Preemptible
  - entity: sensor.web_888_total_session_hours
    name: Total Session Hours
```

## Reporter Config Card

Show auto-discovered reporter settings:

```yaml
type: entities
title: Reporter Config
entities:
  - entity: sensor.web_888_reporter_callsign
    name: Callsign
  - entity: sensor.web_888_reporter_grid
    name: Grid Square
  - entity: sensor.web_888_reporter_snr_correction
    name: SNR Correction
  - entity: sensor.web_888_reporter_dt_correction
    name: dT Correction
  - type: divider
  - entity: sensor.web_888_ft8_autorun_channels
    name: FT8 Autorun Slots
  - entity: sensor.web_888_wspr_autorun_channels
    name: WSPR Autorun Slots
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
  - entity: sensor.web_888_total_decodes
    name: Decodes
  - entity: sensor.web_888_cpu_temperature
    name: Temp
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
    entity: sensor.web_888_total_decodes
    name: Decodes
    icon: mdi:counter
    color: blue
  - type: tile
    entity: sensor.web_888_ft8_channels
    name: FT8 Channels
    icon: mdi:radio-tower
    color: purple
  - type: tile
    entity: sensor.web_888_gps_in_solution
    name: GPS Sats
    icon: mdi:satellite-variant
    color: green
  - type: tile
    entity: sensor.web_888_sequence_errors
    name: Seq Errors
    icon: mdi:alert-circle
    color: green
    card_mod:
      style: |
        ha-card {
          {% set val = states(config.entity) | float(0) %}
          {% if val > 0 %} --tile-color: #ffa600;
          {% endif %}
        }
```

## Channel Activity Card (WebSocket Mode)

Monitor active decoder channels with v1.2.1 session info:

```yaml
type: entities
title: FT8 Channels
entities:
  - entity: sensor.web_888_channel_2_frequency
    name: FT8-80m
    secondary_info: attribute
    attribute: session_time
  - entity: sensor.web_888_channel_2_decoded
    name: Decodes
  - type: divider
  - entity: sensor.web_888_channel_4_frequency
    name: FT8-40m
    secondary_info: attribute
    attribute: session_time
  - entity: sensor.web_888_channel_4_decoded
    name: Decodes
  - type: divider
  - entity: sensor.web_888_channel_6_frequency
    name: FT8-20m
    secondary_info: attribute
    attribute: session_time
  - entity: sensor.web_888_channel_6_decoded
    name: Decodes
```

## History Graph - Decodes

Track decode rate over time:

```yaml
type: history-graph
title: Web-888 Decode Activity
hours_to_show: 24
entities:
  - entity: sensor.web_888_ft8_total_decodes
    name: FT8
  - entity: sensor.web_888_wspr_total_decodes
    name: WSPR
  - entity: sensor.web_888_total_decodes
    name: Total
```

## History Graph - System Health

Track thermal and diagnostic counters:

```yaml
type: history-graph
title: Web-888 System Health
hours_to_show: 24
entities:
  - entity: sensor.web_888_cpu_temperature
    name: CPU Temp
  - entity: sensor.web_888_audio_dropped
    name: Dropped
  - entity: sensor.web_888_sequence_errors
    name: Seq Errors
```

## History Graph - GPS

Track GPS performance:

```yaml
type: history-graph
title: Web-888 GPS Performance
hours_to_show: 24
entities:
  - entity: sensor.web_888_gps_tracking
    name: Tracking
  - entity: sensor.web_888_gps_in_solution
    name: In Solution
  - entity: sensor.web_888_gps_avg_snr
    name: Avg SNR
```

## Device Config Card (v1.2.0+)

Show device configuration:

```yaml
type: entities
title: Web-888 Config
entities:
  - entity: sensor.web_888_cfg_rx_name
    name: Device Name
  - entity: sensor.web_888_cfg_rx_antenna
    name: Antenna
  - entity: sensor.web_888_cfg_inactivity_timeout
    name: Timeout (min)
  - entity: sensor.web_888_cfg_camping_slots
    name: Camping Slots
  - type: divider
  - entity: binary_sensor.web_888_cfg_gps_enabled
    name: GPS Enabled
  - entity: binary_sensor.web_888_cfg_wspr_enabled
    name: WSPR Enabled
  - entity: binary_sensor.web_888_cfg_server_enabled
    name: Server Enabled
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
      - entity: sensor.web_888_10_1_1_28_ft8_total_decodes
      - entity: sensor.web_888_10_1_1_28_total_session_hours
  - type: entities
    title: WSPR Receiver
    entities:
      - entity: binary_sensor.web_888_10_1_1_29_connected
      - entity: sensor.web_888_10_1_1_29_users
      - entity: sensor.web_888_10_1_1_29_wspr_total_decodes
      - entity: sensor.web_888_10_1_1_29_total_session_hours
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
  - platform: state
    entity_id: binary_sensor.web_888_thermal_warning
    to: "on"
    for:
      minutes: 5
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 Temperature Warning"
      message: "CPU temperature is {{ states('sensor.web_888_cpu_temperature') }}°C"
```

### Alert on Diagnostic Errors (v1.2.1)

```yaml
alias: "Alert: Web-888 Errors Detected"
trigger:
  - platform: numeric_state
    entity_id: sensor.web_888_sequence_errors
    above: 0
  - platform: numeric_state
    entity_id: sensor.web_888_realtime_errors
    above: 0
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 Error Alert"
      message: >
        Sequence: {{ states('sensor.web_888_sequence_errors') }},
        Realtime: {{ states('sensor.web_888_realtime_errors') }}
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
      message: >
        Daily decodes - FT8: {{ states('sensor.web_888_ft8_total_decodes') }},
        WSPR: {{ states('sensor.web_888_wspr_total_decodes') }},
        Total: {{ states('sensor.web_888_total_decodes') }}
```

### Monitor Channel Uptime (v1.2.1)

```yaml
alias: "Alert: Channel Runtime Over 500 Hours"
trigger:
  - platform: numeric_state
    entity_id: sensor.web_888_total_session_hours
    above: 500
action:
  - service: notify.mobile_app
    data:
      title: "Web-888 Long Runtime"
      message: "Total channel runtime: {{ states('sensor.web_888_total_session_hours') | round(1) }} hours"
```

---

## Pre-built Dashboards

Full dashboard YAML files are available in the repository:

- [`examples/entities-card.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/entities-card.yaml) - Comprehensive entities card
- [`examples/glance-card.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/glance-card.yaml) - Compact glance view
- [`examples/history-graph.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/history-graph.yaml) - Historical charts
- [`examples/ft8-monitoring.yaml`](https://github.com/pentafive/web888-ha-bridge/blob/main/examples/ft8-monitoring.yaml) - FT8/WSPR focused dashboard

---

## Dashboard Generator

Use the interactive dashboard generator at [`docs/dashboard-generator.html`](https://github.com/pentafive/web888-ha-bridge/blob/main/docs/dashboard-generator.html) to create custom dashboard YAML.

---

## Contributing

Share your dashboard configs! Open a PR or submit an issue with your setup.
