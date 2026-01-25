# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Exponential backoff reconnection logic (5s → 60s)
- Comprehensive logging with configurable levels

### Technical Notes

- Requires Python 3.10+
- Compatible with Home Assistant 2024.1.0+
- WebSocket protocol based on KiwiSDR admin interface

## [Unreleased]

### Planned

- Dashboard example configurations
- Additional diagnostic sensors
- HACS marketplace submission
