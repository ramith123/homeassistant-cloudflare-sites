"""Switch platform for Cloudflare Under Attack integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CloudflareConfigEntry
from .const import DOMAIN, SECURITY_LEVEL_UNDER_ATTACK
from .coordinator import (
    CloudflareRuleData,
    CloudflareUnderAttackCoordinator,
    CloudflareZoneData,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudflareConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare Under Attack switches."""
    coordinator = entry.runtime_data.coordinator

    entities: list[SwitchEntity] = [
        CloudflareUnderAttackSwitch(coordinator, zone_id)
        for zone_id in coordinator.data
    ]

    # Create initial rule switches
    known_rule_keys: set[str] = set()
    for zone_id, zone_data in coordinator.data.items():
        for rule_id in zone_data.rules:
            key = f"{zone_id}_{rule_id}"
            known_rule_keys.add(key)
            entities.append(CloudflareRuleSwitch(coordinator, zone_id, rule_id))

    async_add_entities(entities)

    # Listen for coordinator updates to discover new rules
    @callback
    def _async_check_new_rules() -> None:
        new_entities: list[SwitchEntity] = []
        for zone_id, zone_data in coordinator.data.items():
            for rule_id in zone_data.rules:
                key = f"{zone_id}_{rule_id}"
                if key not in known_rule_keys:
                    known_rule_keys.add(key)
                    new_entities.append(
                        CloudflareRuleSwitch(coordinator, zone_id, rule_id)
                    )
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(
        coordinator.async_add_listener(_async_check_new_rules)
    )


class CloudflareUnderAttackSwitch(
    CoordinatorEntity[CloudflareUnderAttackCoordinator], SwitchEntity
):
    """Switch to toggle Cloudflare Under Attack mode for a zone."""

    _attr_has_entity_name = True
    _attr_name = "Under Attack Mode"

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


class CloudflareRuleSwitch(
    CoordinatorEntity[CloudflareUnderAttackCoordinator], SwitchEntity
):
    """Switch to toggle a Cloudflare WAF custom rule on/off."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CloudflareUnderAttackCoordinator,
        zone_id: str,
        rule_id: str,
    ) -> None:
        """Initialize the rule switch."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._rule_id = rule_id
        self._attr_unique_id = f"{zone_id}_rule_{rule_id}"

    @property
    def available(self) -> bool:
        """Return True if the rule still exists."""
        return (
            super().available
            and self._zone_id in self.coordinator.data
            and self._rule_id in self.coordinator.data[self._zone_id].rules
        )

    @property
    def _rule_data(self) -> CloudflareRuleData:
        """Get the rule data from coordinator."""
        return self.coordinator.data[self._zone_id].rules[self._rule_id]

    @property
    def name(self) -> str:
        """Return the rule description as entity name."""
        return self._rule_data.description or f"Rule {self._rule_id[:8]}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group under the zone."""
        zone_data = self.coordinator.data[self._zone_id]
        return DeviceInfo(
            identifiers={(DOMAIN, self._zone_id)},
            name=zone_data.zone_name,
            manufacturer="Cloudflare",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the rule is enabled."""
        return self._rule_data.enabled

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes for the rule."""
        rule = self._rule_data
        return {
            "rule_id": rule.rule_id,
            "ruleset_id": rule.ruleset_id,
            "action": rule.action,
            "expression": rule.expression,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the WAF rule."""
        await self.coordinator.async_set_rule_enabled(
            self._zone_id, self._rule_data.ruleset_id, self._rule_id, True
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the WAF rule."""
        await self.coordinator.async_set_rule_enabled(
            self._zone_id, self._rule_data.ruleset_id, self._rule_id, False
        )
