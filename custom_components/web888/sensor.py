"""Sensor platform for Web-888 SDR Monitor integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfDataRate,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_CHANNELS,
    CONF_ENABLE_SATELLITES,
    DEFAULT_ENABLE_CHANNELS,
    DEFAULT_ENABLE_SATELLITES,
    DOMAIN,
    MAX_SATELLITES,
    MODE_HTTP,
    NUM_CHANNELS,
)
from .coordinator import Web888Coordinator


@dataclass(frozen=True, kw_only=True)
class Web888SensorEntityDescription(SensorEntityDescription):
    """Describes Web-888 sensor entity."""

    value_fn: str  # Key in coordinator data dict
    websocket_only: bool = False  # True if sensor requires WebSocket mode


# Device-level sensor descriptions
SENSOR_DESCRIPTIONS: tuple[Web888SensorEntityDescription, ...] = (
    Web888SensorEntityDescription(
        key="users",
        translation_key="users",
        name="Users",
        native_unit_of_measurement="users",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="users",
    ),
    Web888SensorEntityDescription(
        key="users_max",
        translation_key="users_max",
        name="Users Max",
        native_unit_of_measurement="users",
        icon="mdi:account-multiple-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="users_max",
    ),
    Web888SensorEntityDescription(
        key="uptime",
        translation_key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="uptime_seconds",
    ),
    Web888SensorEntityDescription(
        key="cpu_temp",
        translation_key="cpu_temp",
        name="CPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cpu_temp_c",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="gps_satellites",
        translation_key="gps_satellites",
        name="GPS Satellites",
        native_unit_of_measurement="satellites",
        icon="mdi:satellite-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_satellites",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="gps_fixes",
        translation_key="gps_fixes",
        name="GPS Fixes",
        native_unit_of_measurement="fixes",
        icon="mdi:crosshairs-gps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_fixes",
    ),
    Web888SensorEntityDescription(
        key="grid_square",
        translation_key="grid_square",
        name="Grid Square",
        icon="mdi:grid",
        value_fn="grid_square",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="latitude",
        translation_key="latitude",
        name="Latitude",
        icon="mdi:latitude",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="latitude",
    ),
    Web888SensorEntityDescription(
        key="longitude",
        translation_key="longitude",
        name="Longitude",
        icon="mdi:longitude",
        native_unit_of_measurement="°",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="longitude",
    ),
    Web888SensorEntityDescription(
        key="total_decodes",
        translation_key="total_decodes",
        name="Total Decodes",
        native_unit_of_measurement="decodes",
        icon="mdi:radio-tower",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn="total_decodes",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="audio_bandwidth",
        translation_key="audio_bandwidth",
        name="Audio Bandwidth",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="audio_bandwidth",
        websocket_only=True,
    ),
    # New sensors from /status endpoint (HTTP compatible)
    Web888SensorEntityDescription(
        key="snr_all",
        translation_key="snr_all",
        name="SNR All Bands",
        native_unit_of_measurement="dB",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
        value_fn="snr_all",
    ),
    Web888SensorEntityDescription(
        key="snr_hf",
        translation_key="snr_hf",
        name="SNR HF",
        native_unit_of_measurement="dB",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
        value_fn="snr_hf",
    ),
    Web888SensorEntityDescription(
        key="gps_good",
        translation_key="gps_good",
        name="GPS Good Satellites",
        native_unit_of_measurement="satellites",
        icon="mdi:satellite-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_good",
    ),
    Web888SensorEntityDescription(
        key="altitude",
        translation_key="altitude",
        name="Altitude",
        native_unit_of_measurement="m",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:altimeter",
        value_fn="altitude",
    ),
    Web888SensorEntityDescription(
        key="bands",
        translation_key="bands",
        name="Frequency Bands",
        icon="mdi:radio-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="bands",
    ),
    Web888SensorEntityDescription(
        key="device_status",
        translation_key="device_status",
        name="Device Status",
        icon="mdi:shield-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="device_status",
    ),
    Web888SensorEntityDescription(
        key="adc_overflow",
        translation_key="adc_overflow",
        name="ADC Overflow Count",
        native_unit_of_measurement="overflows",
        icon="mdi:chart-bell-curve",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="adc_overflow",
    ),
    # v1.1.0: Additional CPU/System sensors (WebSocket only)
    Web888SensorEntityDescription(
        key="cpu_freq",
        translation_key="cpu_freq",
        name="CPU Frequency",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn="cpu_freq_mhz",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:cpu-64-bit",
        value_fn="cpu_usage_avg",
        websocket_only=True,
    ),
    # v1.1.0: Bandwidth sensors (WebSocket only)
    Web888SensorEntityDescription(
        key="waterfall_bandwidth",
        translation_key="waterfall_bandwidth",
        name="Waterfall Bandwidth",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chart-waterfall",
        value_fn="waterfall_bandwidth",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="http_bandwidth",
        translation_key="http_bandwidth",
        name="HTTP Bandwidth",
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:web",
        value_fn="http_bandwidth",
        websocket_only=True,
    ),
    # v1.1.0: Audio diagnostics (WebSocket only)
    Web888SensorEntityDescription(
        key="audio_dropped",
        translation_key="audio_dropped",
        name="Audio Dropped",
        native_unit_of_measurement="packets",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:speaker-off",
        value_fn="audio_dropped",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="audio_underruns",
        translation_key="audio_underruns",
        name="Audio Underruns",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:speedometer-slow",
        value_fn="audio_underruns",
        websocket_only=True,
    ),
    # v1.2.1: Sequence and realtime diagnostic errors
    Web888SensorEntityDescription(
        key="sequence_errors",
        translation_key="sequence_errors",
        name="Sequence Errors",
        native_unit_of_measurement="errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
        value_fn="sequence_errors",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="realtime_errors",
        translation_key="realtime_errors",
        name="Realtime Errors",
        native_unit_of_measurement="errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-alert-outline",
        value_fn="realtime_errors",
        websocket_only=True,
    ),
    # v1.2.1: Channel aggregate metrics
    Web888SensorEntityDescription(
        key="total_session_hours",
        translation_key="total_session_hours",
        name="Total Session Hours",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-outline",
        value_fn="total_session_hours",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="preemptible_channels",
        translation_key="preemptible_channels",
        name="Preemptible Channels",
        native_unit_of_measurement="channels",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:swap-horizontal",
        value_fn="preemptible_channels",
        websocket_only=True,
    ),
    # v1.1.0: Extended GPS sensors (WebSocket only)
    Web888SensorEntityDescription(
        key="gps_tracking",
        translation_key="gps_tracking",
        name="GPS Tracking",
        native_unit_of_measurement="satellites",
        icon="mdi:satellite-uplink",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_tracking",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="gps_in_solution",
        translation_key="gps_in_solution",
        name="GPS In Solution",
        native_unit_of_measurement="satellites",
        icon="mdi:satellite-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_in_solution",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="gps_avg_snr",
        translation_key="gps_avg_snr",
        name="GPS Avg SNR",
        native_unit_of_measurement="dB",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:signal",
        value_fn="gps_avg_snr",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="adc_clock",
        translation_key="adc_clock",
        name="ADC Clock",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-digital",
        value_fn="adc_clock_mhz",
        websocket_only=True,
    ),
    # v1.1.0: HTTP /status fields (available in both modes)
    Web888SensorEntityDescription(
        key="gps_fixes_per_min",
        translation_key="gps_fixes_per_min",
        name="GPS Fixes/min",
        native_unit_of_measurement="fixes/min",
        icon="mdi:crosshairs-gps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_fixes_per_min",
    ),
    Web888SensorEntityDescription(
        key="gps_fixes_per_hour",
        translation_key="gps_fixes_per_hour",
        name="GPS Fixes/hour",
        native_unit_of_measurement="fixes/hour",
        icon="mdi:crosshairs-gps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="gps_fixes_per_hour",
    ),
    Web888SensorEntityDescription(
        key="freq_offset",
        translation_key="freq_offset",
        name="Frequency Offset",
        native_unit_of_measurement="Hz",
        device_class=SensorDeviceClass.FREQUENCY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:tune-vertical",
        value_fn="freq_offset",
    ),
    # v1.1.0: Reporter config (auto-discovered from WebSocket cfg)
    Web888SensorEntityDescription(
        key="reporter_callsign",
        translation_key="reporter_callsign",
        name="Reporter Callsign",
        icon="mdi:account-badge",
        value_fn="reporter_callsign",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="reporter_grid",
        translation_key="reporter_grid",
        name="Reporter Grid",
        icon="mdi:grid",
        value_fn="reporter_grid",
        websocket_only=True,
    ),
    # v1.1.0: Channel type counts (WebSocket only)
    Web888SensorEntityDescription(
        key="ft8_channels",
        translation_key="ft8_channels",
        name="FT8 Channels",
        native_unit_of_measurement="channels",
        icon="mdi:radio-tower",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="ft8_channels",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="wspr_channels",
        translation_key="wspr_channels",
        name="WSPR Channels",
        native_unit_of_measurement="channels",
        icon="mdi:broadcast",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="wspr_channels",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="user_channels",
        translation_key="user_channels",
        name="User Channels",
        native_unit_of_measurement="channels",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="user_channels",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="idle_channels",
        translation_key="idle_channels",
        name="Idle Channels",
        native_unit_of_measurement="channels",
        icon="mdi:sleep",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn="idle_channels",
        websocket_only=True,
    ),
    # v1.1.0: Per-mode decode totals (WebSocket only)
    Web888SensorEntityDescription(
        key="ft8_total_decodes",
        translation_key="ft8_total_decodes",
        name="FT8 Total Decodes",
        native_unit_of_measurement="decodes",
        icon="mdi:radio-tower",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn="ft8_total_decodes",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="wspr_total_decodes",
        translation_key="wspr_total_decodes",
        name="WSPR Total Decodes",
        native_unit_of_measurement="decodes",
        icon="mdi:broadcast",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn="wspr_total_decodes",
        websocket_only=True,
    ),
    # v1.1.0: WSPR reporter config (for wsprnet.org)
    Web888SensorEntityDescription(
        key="wspr_callsign",
        translation_key="wspr_callsign",
        name="WSPR Callsign",
        icon="mdi:account-badge",
        value_fn="wspr_callsign",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="wspr_grid",
        translation_key="wspr_grid",
        name="WSPR Grid",
        icon="mdi:grid",
        value_fn="wspr_grid",
        websocket_only=True,
    ),
    # v1.1.0: FT8 reporter config (for PSKReporter) - often empty, uses WSPR as fallback
    Web888SensorEntityDescription(
        key="ft8_callsign",
        translation_key="ft8_callsign",
        name="FT8 Callsign",
        icon="mdi:account-badge-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="ft8_callsign",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="ft8_grid",
        translation_key="ft8_grid",
        name="FT8 Grid",
        icon="mdi:grid-large",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="ft8_grid",
        websocket_only=True,
    ),
    # v1.1.0: FT8 correction values (applied before reporting to PSKReporter)
    Web888SensorEntityDescription(
        key="reporter_snr_correction",
        translation_key="reporter_snr_correction",
        name="FT8 SNR Correction",
        native_unit_of_measurement="dB",
        icon="mdi:signal-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="reporter_snr_correction",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="reporter_dt_correction",
        translation_key="reporter_dt_correction",
        name="FT8 dT Correction",
        native_unit_of_measurement="s",
        icon="mdi:timer-cog",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="reporter_dt_correction",
        websocket_only=True,
    ),
    # v1.1.0: Autorun channel counts (WebSocket only, configured in device)
    Web888SensorEntityDescription(
        key="wspr_autorun_channels",
        translation_key="wspr_autorun_channels",
        name="WSPR Autorun Channels",
        native_unit_of_measurement="channels",
        icon="mdi:broadcast",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="wspr_autorun_channels",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="ft8_autorun_channels",
        translation_key="ft8_autorun_channels",
        name="FT8 Autorun Channels",
        native_unit_of_measurement="channels",
        icon="mdi:radio-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="ft8_autorun_channels",
        websocket_only=True,
    ),
    # === v1.2.0: Device Config Sensors (WebSocket only) ===
    # Calibration
    Web888SensorEntityDescription(
        key="cfg_s_meter_cal",
        translation_key="cfg_s_meter_cal",
        name="S-Meter Calibration",
        native_unit_of_measurement="dB",
        icon="mdi:gauge",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_s_meter_cal",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_waterfall_cal",
        translation_key="cfg_waterfall_cal",
        name="Waterfall Calibration",
        native_unit_of_measurement="dB",
        icon="mdi:chart-waterfall",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_waterfall_cal",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_overload_mute",
        translation_key="cfg_overload_mute",
        name="Overload Mute Threshold",
        native_unit_of_measurement="dB",
        icon="mdi:volume-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_overload_mute",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_clk_adj",
        translation_key="cfg_clk_adj",
        name="Clock Adjustment",
        icon="mdi:clock-edit",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_clk_adj",
        websocket_only=True,
    ),
    # Session/access config
    Web888SensorEntityDescription(
        key="cfg_inactivity_timeout",
        translation_key="cfg_inactivity_timeout",
        name="Inactivity Timeout",
        native_unit_of_measurement="min",
        icon="mdi:timer-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_inactivity_timeout",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_chan_no_pwd",
        translation_key="cfg_chan_no_pwd",
        name="Password-Free Channels",
        native_unit_of_measurement="channels",
        icon="mdi:lock-open",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_chan_no_pwd",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_camping_slots",
        translation_key="cfg_camping_slots",
        name="Camping Slots",
        native_unit_of_measurement="slots",
        icon="mdi:tent",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_camping_slots",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_api_channels",
        translation_key="cfg_api_channels",
        name="API Channels",
        native_unit_of_measurement="channels",
        icon="mdi:api",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_api_channels",
        websocket_only=True,
    ),
    # Network config
    Web888SensorEntityDescription(
        key="cfg_static_ip",
        translation_key="cfg_static_ip",
        name="Configured IP",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_static_ip",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_port",
        translation_key="cfg_port",
        name="Service Port",
        icon="mdi:network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_port",
        websocket_only=True,
    ),
    # Device info from config
    Web888SensorEntityDescription(
        key="cfg_rx_name",
        translation_key="cfg_rx_name",
        name="Config Device Name",
        icon="mdi:label",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_rx_name",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_rx_antenna",
        translation_key="cfg_rx_antenna",
        name="Config Antenna",
        icon="mdi:antenna",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_rx_antenna",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_rx_asl",
        translation_key="cfg_rx_asl",
        name="Config Altitude ASL",
        native_unit_of_measurement="m",
        icon="mdi:altimeter",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_rx_asl",
        websocket_only=True,
    ),
    Web888SensorEntityDescription(
        key="cfg_owner_email",
        translation_key="cfg_owner_email",
        name="Owner Email",
        icon="mdi:email",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn="cfg_owner_email",
        websocket_only=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Web-888 sensors based on a config entry."""
    coordinator: Web888Coordinator = hass.data[DOMAIN][entry.entry_id]
    is_http_mode = coordinator.mode == MODE_HTTP

    entities: list[SensorEntity] = []

    # Add device-level sensors (skip WebSocket-only sensors in HTTP mode)
    for description in SENSOR_DESCRIPTIONS:
        if description.websocket_only and is_http_mode:
            continue
        entities.append(Web888Sensor(coordinator, description))

    # Add per-channel sensors if enabled (WebSocket mode only - HTTP doesn't provide channel data)
    if not is_http_mode:
        enable_channels = entry.options.get(
            CONF_ENABLE_CHANNELS,
            entry.data.get(CONF_ENABLE_CHANNELS, DEFAULT_ENABLE_CHANNELS),
        )

        if enable_channels:
            for i in range(NUM_CHANNELS):
                entities.append(Web888ChannelFrequencySensor(coordinator, i))
                entities.append(Web888ChannelModeSensor(coordinator, i))
                entities.append(Web888ChannelDecodedSensor(coordinator, i))

    # v1.1.0: Add per-satellite sensors if enabled (WebSocket mode only)
    if not is_http_mode:
        enable_satellites = entry.options.get(
            CONF_ENABLE_SATELLITES,
            entry.data.get(CONF_ENABLE_SATELLITES, DEFAULT_ENABLE_SATELLITES),
        )

        if enable_satellites:
            for i in range(MAX_SATELLITES):
                entities.append(Web888SatelliteSNRSensor(coordinator, i))
                entities.append(Web888SatelliteRSSISensor(coordinator, i))
                entities.append(Web888SatelliteAzimuthSensor(coordinator, i))
                entities.append(Web888SatelliteElevationSensor(coordinator, i))
                entities.append(Web888SatelliteInSolutionSensor(coordinator, i))

    async_add_entities(entities)


class Web888Sensor(CoordinatorEntity[Web888Coordinator], SensorEntity):
    """Representation of a Web-888 sensor."""

    entity_description: Web888SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Web888Coordinator,
        description: Web888SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.value_fn)


class Web888ChannelSensorBase(CoordinatorEntity[Web888Coordinator], SensorEntity):
    """Base class for per-channel sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Web888Coordinator,
        channel_index: int,
    ) -> None:
        """Initialize the channel sensor."""
        super().__init__(coordinator)
        self._channel_index = channel_index
        self._attr_device_info = coordinator.device_info

    def _get_channel_data(self) -> dict[str, Any] | None:
        """Get data for this channel."""
        if self.coordinator.data is None:
            return None
        channels = self.coordinator.data.get("channels", [])
        if self._channel_index < len(channels):
            return channels[self._channel_index]
        return None


class Web888ChannelFrequencySensor(Web888ChannelSensorBase):
    """Sensor for channel frequency."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        channel_index: int,
    ) -> None:
        """Initialize the channel frequency sensor."""
        super().__init__(coordinator, channel_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_channel_{channel_index}_frequency"
        self._attr_name = f"Channel {channel_index} Frequency"
        self._attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
        self._attr_device_class = SensorDeviceClass.FREQUENCY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:sine-wave"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int | None:
        """Return the frequency in Hz."""
        channel = self._get_channel_data()
        if channel is None:
            return None
        return channel.get("frequency_hz", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        channel = self._get_channel_data()
        if channel is None:
            return {}
        freq_hz = channel.get("frequency_hz", 0)
        return {
            "frequency_khz": round(freq_hz / 1000, 2) if freq_hz else 0,
            "frequency_mhz": round(freq_hz / 1_000_000, 4) if freq_hz else 0,
            "channel_name": channel.get("name", ""),
            "active": channel.get("active", False),
            # v1.1.0: Channel type info
            "channel_type": channel.get("channel_type", ""),
            "extension": channel.get("extension", ""),
            "is_extension": channel.get("is_extension", False),
            "client_ip": channel.get("client_ip", ""),
            # v1.2.1: Session runtime and preemptible status
            "session_time": channel.get("session_time", ""),
            "session_seconds": channel.get("session_seconds", 0),
            "preemptible": channel.get("preemptible", False),
        }


class Web888ChannelModeSensor(Web888ChannelSensorBase):
    """Sensor for channel mode."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        channel_index: int,
    ) -> None:
        """Initialize the channel mode sensor."""
        super().__init__(coordinator, channel_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_channel_{channel_index}_mode"
        self._attr_name = f"Channel {channel_index} Mode"
        self._attr_icon = "mdi:radio"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        """Return the mode (USB, LSB, etc.)."""
        channel = self._get_channel_data()
        if channel is None:
            return None
        mode = channel.get("mode", "")
        return mode.upper() if mode else "Idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        channel = self._get_channel_data()
        if channel is None:
            return {}
        return {
            # v1.1.0: Channel type info
            "channel_type": channel.get("channel_type", ""),
            "extension": channel.get("extension", ""),
            "is_extension": channel.get("is_extension", False),
        }


class Web888ChannelDecodedSensor(Web888ChannelSensorBase):
    """Sensor for channel decoded count."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        channel_index: int,
    ) -> None:
        """Initialize the channel decoded count sensor."""
        super().__init__(coordinator, channel_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_channel_{channel_index}_decoded"
        self._attr_name = f"Channel {channel_index} Decoded"
        self._attr_native_unit_of_measurement = "decodes"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:counter"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int | None:
        """Return the decoded count."""
        channel = self._get_channel_data()
        if channel is None:
            return None
        return channel.get("decoded_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        channel = self._get_channel_data()
        if channel is None:
            return {}
        return {
            # v1.1.0: Channel type info (useful for knowing if FT8/WSPR decode)
            "channel_type": channel.get("channel_type", ""),
            "extension": channel.get("extension", ""),
            "is_extension": channel.get("is_extension", False),
        }


# v1.1.0: Per-satellite sensors for security monitoring
class Web888SatelliteSensorBase(CoordinatorEntity[Web888Coordinator], SensorEntity):
    """Base class for per-satellite sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite sensor."""
        super().__init__(coordinator)
        self._satellite_index = satellite_index
        self._attr_device_info = coordinator.device_info
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _get_satellite_data(self) -> dict[str, Any] | None:
        """Get data for this satellite."""
        if self.coordinator.data is None:
            return None
        satellites = self.coordinator.data.get("satellites", [])
        if self._satellite_index < len(satellites):
            return satellites[self._satellite_index]
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Satellite sensor is only available if we have data for this slot
        return self._get_satellite_data() is not None


class Web888SatelliteSNRSensor(Web888SatelliteSensorBase):
    """Sensor for satellite SNR - security monitoring for interference detection."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite SNR sensor."""
        super().__init__(coordinator, satellite_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sat_{satellite_index}_snr"
        self._attr_name = f"Satellite {satellite_index} SNR"
        self._attr_native_unit_of_measurement = "dB"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:satellite-variant"

    @property
    def native_value(self) -> int | None:
        """Return the satellite SNR."""
        sat = self._get_satellite_data()
        if sat is None:
            return None
        return sat.get("snr", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        sat = self._get_satellite_data()
        if sat is None:
            return {}
        return {
            "system": sat.get("system", ""),
            "prn": sat.get("prn", 0),
            "channel": sat.get("channel", 0),
            "in_solution": sat.get("in_solution", False),
        }


class Web888SatelliteRSSISensor(Web888SatelliteSensorBase):
    """Sensor for satellite RSSI."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite RSSI sensor."""
        super().__init__(coordinator, satellite_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sat_{satellite_index}_rssi"
        self._attr_name = f"Satellite {satellite_index} RSSI"
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:signal-cellular-3"

    @property
    def native_value(self) -> int | None:
        """Return the satellite RSSI."""
        sat = self._get_satellite_data()
        if sat is None:
            return None
        return sat.get("rssi", 0)


class Web888SatelliteAzimuthSensor(Web888SatelliteSensorBase):
    """Sensor for satellite azimuth - useful for LOS analysis."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite azimuth sensor."""
        super().__init__(coordinator, satellite_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sat_{satellite_index}_azimuth"
        self._attr_name = f"Satellite {satellite_index} Azimuth"
        self._attr_native_unit_of_measurement = "°"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:compass"

    @property
    def native_value(self) -> int | None:
        """Return the satellite azimuth."""
        sat = self._get_satellite_data()
        if sat is None:
            return None
        return sat.get("azimuth", 0)


class Web888SatelliteElevationSensor(Web888SatelliteSensorBase):
    """Sensor for satellite elevation - useful for LOS analysis."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite elevation sensor."""
        super().__init__(coordinator, satellite_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sat_{satellite_index}_elevation"
        self._attr_name = f"Satellite {satellite_index} Elevation"
        self._attr_native_unit_of_measurement = "°"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:angle-acute"

    @property
    def native_value(self) -> int | None:
        """Return the satellite elevation."""
        sat = self._get_satellite_data()
        if sat is None:
            return None
        return sat.get("elevation", 0)


class Web888SatelliteInSolutionSensor(Web888SatelliteSensorBase):
    """Sensor for whether satellite is in position solution."""

    def __init__(
        self,
        coordinator: Web888Coordinator,
        satellite_index: int,
    ) -> None:
        """Initialize the satellite in-solution sensor."""
        super().__init__(coordinator, satellite_index)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sat_{satellite_index}_in_solution"
        self._attr_name = f"Satellite {satellite_index} In Solution"
        self._attr_icon = "mdi:check-circle"

    @property
    def native_value(self) -> str | None:
        """Return whether satellite is in solution."""
        sat = self._get_satellite_data()
        if sat is None:
            return None
        return "Yes" if sat.get("in_solution", False) else "No"
