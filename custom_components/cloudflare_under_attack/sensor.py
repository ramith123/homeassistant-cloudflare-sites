"""Sensor platform for Cloudflare Under Attack integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CloudflareConfigEntry
from .const import DOMAIN, SECURITY_LEVELS
from .coordinator import CloudflareUnderAttackCoordinator, CloudflareZoneData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudflareConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare security level sensors."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        CloudflareSecurityLevelSensor(coordinator, zone_id)
        for zone_id in coordinator.data
    )


class CloudflareSecurityLevelSensor(
    CoordinatorEntity[CloudflareUnderAttackCoordinator], SensorEntity
):
    """Sensor showing the current Cloudflare security level for a zone."""

    _attr_has_entity_name = True
    _attr_name = "Security Level"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SECURITY_LEVELS

    def __init__(
        self,
        coordinator: CloudflareUnderAttackCoordinator,
        zone_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"{zone_id}_security_level"

    @property
    def _zone_data(self) -> CloudflareZoneData:
        """Get the zone data from coordinator."""
        return self.coordinator.data[self._zone_id]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group entities under the zone."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._zone_id)},
            name=self._zone_data.zone_name,
            manufacturer="Cloudflare",
        )

    @property
    def native_value(self) -> str:
        """Return the current security level."""
        return self._zone_data.security_level

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "zone_id": self._zone_data.zone_id,
            "zone_name": self._zone_data.zone_name,
            "previous_security_level": self._zone_data.previous_security_level,
        }
