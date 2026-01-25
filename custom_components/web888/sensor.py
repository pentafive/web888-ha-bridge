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
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_CHANNELS,
    DEFAULT_ENABLE_CHANNELS,
    DOMAIN,
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
        websocket_only=True,
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
        websocket_only=True,
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
