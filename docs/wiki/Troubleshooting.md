# Troubleshooting

Common issues and solutions for Web-888 HA Bridge.

## HACS Integration Issues

### Integration not appearing after install

**Solutions:**
1. Restart Home Assistant (not just reload)
2. Clear browser cache
3. Check HACS → Integrations → Web-888 SDR Monitor is installed

### "Cannot connect to Web-888"

**Check:**
1. Web-888 is powered on and network connected
2. Can access Web-888 web interface at `http://<ip>:8073`
3. Correct IP address in configuration
4. No firewall blocking port 8073

**Debug:**
```bash
# From Home Assistant host
curl http://10.1.1.28:8073/status
```

### Sensors showing "Unknown" or "Unavailable"

**For HTTP mode:**
1. Verify `/status` endpoint is accessible
2. Check network connectivity

**For WebSocket mode:**
1. Verify admin password is correct
2. Check if another admin session is active (Web-888 allows limited admin connections)

**Enable debug logging:**
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.web888: debug
```

### Options flow error (500 Internal Server Error)

**Solution:** Update to latest version. This was fixed in recent releases.

If persists:
1. Remove the integration
2. Restart Home Assistant
3. Re-add the integration

### SNR sensors showing "Unknown"

**This is normal if:**
- SNR measurement is disabled on the device
- No measurement has been performed yet (hourly interval by default)
- No free channel slot available for measurement

**To trigger measurement:**
1. Open Web-888 admin page (`http://<ip>:8073/admin`)
2. Click "Measure SNR now" button
3. Wait for next poll interval

### GPS sensors showing "Unknown"

**Causes:**
1. No GPS antenna connected
2. GPS receiver still acquiring fix (can take several minutes)
3. Indoor location with poor GPS reception

**Check:**
- `gps_fixes` sensor - should increase if GPS is working
- `gps_good` sensor - number of satellites with good signal

---

## Docker/MQTT Issues

### Container can't reach Web-888

**Symptoms:** Logs show connection timeouts

**Solutions:**
1. Verify network connectivity: `ping 10.1.1.28` from Docker host
2. Check Docker network mode (host mode may be needed)
3. Verify port 8073 is accessible

### No sensors appearing in Home Assistant

**Check:**
1. MQTT broker is running and accessible
2. MQTT credentials are correct in `.env`
3. MQTT Discovery is enabled in HA (Settings → Devices & Services → MQTT)
4. Discovery prefix matches (default: `homeassistant`)

**Debug:**
```bash
# Check container logs
docker logs web888-ha-bridge

# Verify MQTT messages
mosquitto_sub -h YOUR_MQTT_BROKER -t "homeassistant/#" -v
```

### Sensors show "unavailable"

**Causes:**
1. Bridge lost connection to Web-888
2. Bridge lost connection to MQTT broker
3. Container crashed

**Check:**
```bash
docker logs --tail 50 web888-ha-bridge
docker ps | grep web888
```

### WebSocket reconnection loops

**Symptoms:** Logs show repeated connect/disconnect

**Causes:**
1. Wrong admin password
2. Network instability
3. Web-888 firmware issue

**Solutions:**
1. Verify password in Web-888 admin panel
2. Check network stability
3. Try HTTP mode if WebSocket is unstable

---

## Data Issues

### SNR values seem wrong

**Understanding SNR:**
- 0 or Unknown = Measurement not performed
- 10-15 dB = Noisy RF environment
- 20-30 dB = Good location
- 30+ dB = Excellent/quiet location

**If values seem incorrect:**
1. Verify SNR measurement is enabled in Web-888 admin
2. Check antenna connection
3. Compare with Web-888 web interface values

### GPS coordinates showing (0, 0)

**Causes:**
1. No GPS fix acquired
2. GPS antenna issue
3. Device configured with manual coordinates

**Solutions:**
1. Check `gps_lock` binary sensor
2. Verify GPS antenna is connected
3. Wait for GPS acquisition (can take several minutes after boot)

### Channel sensors all showing "Idle"

**Causes:**
1. No decoders configured on Web-888
2. WebSocket connection not established
3. HTTP mode (channels only available in WebSocket mode)

**Solutions:**
1. Configure decoders in Web-888 admin panel
2. Verify WebSocket mode with correct password
3. Check `enable_channels` option is enabled

### Total decodes not increasing

**Check:**
1. Decoder channels are configured and active
2. Frequencies are appropriate for current propagation
3. Antenna is connected and functioning

---

## Connection Mode Issues

### HTTP mode limitations

**These sensors are NOT available in HTTP mode:**
- CPU Temperature
- Grid Square
- GPS Satellites (total count)
- Total Decodes
- Audio Bandwidth
- All Channel sensors

**Solution:** Configure admin password for WebSocket mode to get full sensor set.

### WebSocket mode not connecting

**Check:**
1. Admin password is correct
2. No other admin sessions active
3. Port 8073 is accessible
4. Web-888 firmware supports admin WebSocket

**Debug:**
```bash
# Test WebSocket connection
wscat -c ws://10.1.1.28:8073/kiwi/12345/admin
```

---

## Performance Issues

### High CPU usage in Home Assistant

**Cause:** Too frequent polling

**Solution:**
- HACS: Options → increase scan interval (30-60 seconds recommended)
- Docker: Increase `SCAN_INTERVAL` in `.env`

### Slow sensor updates

**Causes:**
1. Network latency to Web-888
2. Web-888 under heavy load (many users)
3. Long poll interval configured

**Solutions:**
1. Check network path to device
2. Reduce poll interval (but watch CPU usage)
3. Consider WebSocket mode for faster updates

---

## Getting Help

1. **HACS:** Download diagnostics (Settings → Devices & Services → Web-888 SDR Monitor → device → Download diagnostics)
2. **Docker:** Check logs: `docker logs web888-ha-bridge`
3. Enable debug mode for detailed logging
4. Open an issue with logs and configuration (scrub passwords!)

**Include in bug reports:**
- Home Assistant version
- Integration version
- Connection mode (HTTP/WebSocket)
- Relevant log entries
- Web-888 firmware version (from web interface)
