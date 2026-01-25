# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Web-888 HA Bridge, please report it responsibly:

1. **Do NOT open a public issue**
2. **Email**: pentafive@gmail.com with subject "web888-ha-bridge Security Issue"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity, typically 1-4 weeks

## Security Considerations

### Credentials

- Web-888 admin password is stored in environment variables
- MQTT credentials are stored in environment variables
- **Never commit `.env` files** - only `.env.example` with placeholders
- Consider using Docker secrets or a secrets manager in production

### Network Security

- HTTP mode connects to Web-888 via HTTP (default port 8073)
- WebSocket mode connects to Web-888 admin interface (same port)
- The bridge connects to MQTT broker (default port 1883)
- Consider using MQTT over TLS (port 8883) if your broker supports it
- Restrict network access to the bridge container

### WebSocket Authentication

- Admin password is sent to the Web-888 via WebSocket (unencrypted WS, not WSS)
- **WebSocket mode should only be used on trusted networks**
- HTTP mode is read-only and does not require authentication
- For untrusted networks, use HTTP mode only

### Logging

- Debug mode may log sensitive information
- Keep `DEBUG_MODE=False` in production
- Review logs before sharing in issue reports
- Admin password is never logged

## Scope

This security policy covers:
- The `web888-ha-bridge.py` script
- The `web888_client.py` library
- Docker configuration files
- Example configurations
- HACS custom component

It does NOT cover:
- Web-888/KiwiSDR device security
- Home Assistant security
- MQTT broker security
