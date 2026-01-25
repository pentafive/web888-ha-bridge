"""Binary sensor platform for Web-888 SDR Monitor integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_HTTP
from .coordinator import Web888Coordinator


@dataclass(frozen=True, kw_only=True)
class Web888BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Web-888 binary sensor entity."""

    value_fn: str  # Key in coordinator data dict
    websocket_only: bool = False  # v1.1.0: True if sensor requires WebSocket mode


BINARY_SENSOR_DESCRIPTIONS: tuple[Web888BinarySensorEntityDescription, ...] = (
    Web888BinarySensorEntityDescription(
        key="connected",
        translation_key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn="connected",
    ),
    Web888BinarySensorEntityDescription(
        key="gps_lock",
        translation_key="gps_lock",
        name="GPS Lock",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:crosshairs-gps",
        value_fn="gps_lock",
    ),
    Web888BinarySensorEntityDescription(
        key="antenna_connected",
        translation_key="antenna_connected",
        name="Antenna Connected",
        device_class=BinarySensorDeviceClass.PLUG,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:antenna",
        value_fn="antenna_connected",
    ),
    Web888BinarySensorEntityDescription(
        key="offline",
        translation_key="offline",
        name="Offline",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:cloud-off-outline",
        value_fn="offline",
    ),
    # v1.1.0: GPS Acquiring binary sensor (WebSocket only)
    Web888BinarySensorEntityDescription(
        key="gps_acquiring",
        translation_key="gps_acquiring",
        name="GPS Acquiring",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:satellite-uplink",
        value_fn="gps_acquiring",
        websocket_only=True,
    ),
    # v1.1.0: Thermal Warning binary sensor (WebSocket only)
    Web888BinarySensorEntityDescription(
        key="thermal_warning",
        translation_key="thermal_warning",
        name="Thermal Warning",
        device_class=BinarySensorDeviceClass.HEAT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:thermometer-alert",
        value_fn="thermal_warning",
        websocket_only=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Web-888 binary sensors based on a config entry."""
    coordinator: Web888Coordinator = hass.data[DOMAIN][entry.entry_id]
    is_http_mode = coordinator.mode == MODE_HTTP

    # v1.1.0: Filter out WebSocket-only sensors in HTTP mode
    async_add_entities(
        Web888BinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
        if not (description.websocket_only and is_http_mode)
    )


class Web888BinarySensor(CoordinatorEntity[Web888Coordinator], BinarySensorEntity):
    """Representation of a Web-888 binary sensor."""

    entity_description: Web888BinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Web888Coordinator,
        description: Web888BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.value_fn, False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}

        # Add connection mode for connected sensor
        if self.entity_description.key == "connected":
            return {
                "connection_mode": self.coordinator.mode,
                "host": self.coordinator.host,
                "port": self.coordinator.port,
            }

        # Add GPS details for GPS lock sensor
        if self.entity_description.key == "gps_lock":
            return {
                "grid_square": self.coordinator.data.get("grid_square", ""),
                "satellites": self.coordinator.data.get("gps_satellites", 0),
                "fixes": self.coordinator.data.get("gps_fixes", 0),
            }

        # v1.1.0: Add thermal details for thermal warning sensor
        if self.entity_description.key == "thermal_warning":
            return {
                "threshold": self.coordinator.data.get("thermal_threshold", 70),
                "current_temp": self.coordinator.data.get("cpu_temp_c", 0),
            }

        return {}
