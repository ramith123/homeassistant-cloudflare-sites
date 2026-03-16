"""Switch platform for Cloudflare Under Attack integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CloudflareConfigEntry
from .const import DOMAIN, SECURITY_LEVEL_UNDER_ATTACK
from .coordinator import CloudflareUnderAttackCoordinator, CloudflareZoneData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudflareConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare Under Attack switches."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        CloudflareUnderAttackSwitch(coordinator, zone_id)
        for zone_id in coordinator.data
    )


class CloudflareUnderAttackSwitch(
    CoordinatorEntity[CloudflareUnderAttackCoordinator], SwitchEntity
):
    """Switch to toggle Cloudflare Under Attack mode for a zone."""

    _attr_has_entity_name = True
    _attr_translation_key = "under_attack_mode"

    def __init__(
        self,
        coordinator: CloudflareUnderAttackCoordinator,
        zone_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"{zone_id}_under_attack"

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
    def is_on(self) -> bool:
        """Return True if the zone is in Under Attack mode."""
        return self._zone_data.security_level == SECURITY_LEVEL_UNDER_ATTACK

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Under Attack mode."""
        await self.coordinator.async_set_security_level(
            self._zone_id, SECURITY_LEVEL_UNDER_ATTACK
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Under Attack mode, restoring the previous security level."""
        previous = self._zone_data.previous_security_level
        await self.coordinator.async_set_security_level(self._zone_id, previous)
