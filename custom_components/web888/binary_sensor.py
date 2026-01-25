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

from .const import DOMAIN
from .coordinator import Web888Coordinator


@dataclass(frozen=True, kw_only=True)
class Web888BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Web-888 binary sensor entity."""

    value_fn: str  # Key in coordinator data dict


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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Web-888 binary sensors based on a config entry."""
    coordinator: Web888Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        Web888BinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
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

        return {}
