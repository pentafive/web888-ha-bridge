# Contributing to Web-888 HA Bridge

Thank you for your interest in contributing to Web-888 HA Bridge!

## Ways to Contribute

### Reporting Issues

- **Bug reports**: Include your environment (Python version, Docker version, Web-888 firmware), steps to reproduce, and any relevant logs
- **Feature requests**: Describe the use case and expected behavior
- **Documentation improvements**: Typos, unclear instructions, missing information

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly**: Ensure the bridge connects and publishes data correctly
5. **Commit with clear messages**: Use conventional commits (e.g., `fix:`, `feat:`, `docs:`)
6. **Push and create a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/web888-ha-bridge.git
cd web888-ha-bridge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your test environment settings

# Run in test mode
DEBUG_MODE=True python3 web888-ha-bridge.py
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for new functions
- Keep functions focused and modular
- Run `ruff check .` before committing

### Testing

- Test with both Docker and direct Python execution
- Verify MQTT discovery messages in MQTT Explorer
- Confirm sensors appear correctly in Home Assistant
- Test error handling (disconnect Web-888, stop MQTT broker)
- Test both HTTP and WebSocket modes

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation if adding features
- Update CHANGELOG.md for user-facing changes
- Ensure no sensitive data (IPs, passwords) in commits

## Questions?

- Open an issue for discussion

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
