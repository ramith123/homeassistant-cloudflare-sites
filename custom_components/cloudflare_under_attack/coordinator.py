"""DataUpdateCoordinator for Cloudflare Under Attack integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from cloudflare import AsyncCloudflare
from cloudflare._exceptions import APIError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SECURITY_LEVEL,
    DOMAIN,
    SECURITY_LEVEL_UNDER_ATTACK,
    WAF_CUSTOM_RULES_PHASE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class CloudflareRuleData:
    """Data for a single Cloudflare WAF rule."""

    rule_id: str
    ruleset_id: str
    zone_id: str
    description: str
    action: str
    expression: str
    enabled: bool


@dataclass
class CloudflareZoneData:
    """Data for a single Cloudflare zone."""

    zone_id: str
    zone_name: str
    security_level: str
    previous_security_level: str
    rules: dict[str, CloudflareRuleData]


@dataclass
class CloudflareData:
    """Runtime data stored in entry.runtime_data."""

    client: AsyncCloudflare
    coordinator: CloudflareUnderAttackCoordinator


class CloudflareUnderAttackCoordinator(DataUpdateCoordinator[dict[str, CloudflareZoneData]]):
    """Coordinator that polls Cloudflare security levels for all zones."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AsyncCloudflare,
        zones: list[dict[str, Any]],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.zones = zones
        self._previous_levels: dict[str, str] = {}

    async def _async_update_data(self) -> dict[str, CloudflareZoneData]:
        """Fetch security level for each zone."""
        data: dict[str, CloudflareZoneData] = {}

        for zone in self.zones:
            zone_id = zone["id"]
            zone_name = zone["name"]

            try:
                setting = await self.client.zones.settings.get(
                    zone_id=zone_id,
                    setting_id="security_level",
                )
                security_level = setting.value
            except APIError as err:
                raise UpdateFailed(
                    f"Error fetching security level for {zone_name}: {err}"
                ) from err

            # Track the previous non-under_attack level
            if security_level != SECURITY_LEVEL_UNDER_ATTACK:
                self._previous_levels[zone_id] = security_level

            previous = self._previous_levels.get(zone_id, DEFAULT_SECURITY_LEVEL)

            # Fetch WAF custom rules for this zone
            rules: dict[str, CloudflareRuleData] = {}
            try:
                rulesets_response = await self.client.rulesets.list(zone_id=zone_id)
                for rs in rulesets_response.result:
                    if rs.phase == WAF_CUSTOM_RULES_PHASE:
                        full_ruleset = await self.client.rulesets.get(
                            ruleset_id=rs.id, zone_id=zone_id
                        )
                        if full_ruleset.rules:
                            for rule in full_ruleset.rules:
                                rules[rule.id] = CloudflareRuleData(
                                    rule_id=rule.id,
                                    ruleset_id=rs.id,
                                    zone_id=zone_id,
                                    description=rule.description or "",
                                    action=rule.action or "",
                                    expression=rule.expression or "",
                                    enabled=rule.enabled if rule.enabled is not None else True,
                                )
                        break
            except APIError as err:
                _LOGGER.warning(
                    "Error fetching WAF rules for %s: %s", zone_name, err
                )

            data[zone_id] = CloudflareZoneData(
                zone_id=zone_id,
                zone_name=zone_name,
                security_level=security_level,
                previous_security_level=previous,
                rules=rules,
            )

        return data

    async def async_set_security_level(self, zone_id: str, level: str) -> None:
        """Set the security level for a zone and refresh data."""
        try:
            await self.client.zones.settings.edit(
                zone_id=zone_id,
                setting_id="security_level",
                value=level,
            )
        except APIError as err:
            raise UpdateFailed(
                f"Error setting security level for zone {zone_id}: {err}"
            ) from err

        await self.async_request_refresh()

    async def async_set_rule_enabled(
        self, zone_id: str, ruleset_id: str, rule_id: str, enabled: bool
    ) -> None:
        """Enable or disable a WAF rule and refresh data."""
        rule_data = self.data[zone_id].rules[rule_id]
        try:
            await self.client.rulesets.rules.edit(
                rule_id=rule_id,
                ruleset_id=ruleset_id,
                zone_id=zone_id,
                action=rule_data.action,
                expression=rule_data.expression,
                description=rule_data.description,
                enabled=enabled,
            )
        except APIError as err:
            raise UpdateFailed(
                f"Error setting rule {rule_id} enabled={enabled} for zone {zone_id}: {err}"
            ) from err
        await self.async_request_refresh()
