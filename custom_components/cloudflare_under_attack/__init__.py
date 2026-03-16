"""The Cloudflare Under Attack integration."""

from __future__ import annotations

import logging

from cloudflare import AsyncCloudflare

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_API_TOKEN
from .coordinator import CloudflareData, CloudflareUnderAttackCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR]

type CloudflareConfigEntry = ConfigEntry[CloudflareData]


async def async_setup_entry(hass: HomeAssistant, entry: CloudflareConfigEntry) -> bool:
    """Set up Cloudflare Under Attack from a config entry."""
    token = entry.data[CONF_API_TOKEN]
    client = AsyncCloudflare(api_token=token)

    # Fetch all zones on the account
    zones_response = await client.zones.list()
    zones = [{"id": z.id, "name": z.name} for z in zones_response.result]

    coordinator = CloudflareUnderAttackCoordinator(hass, client, zones)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = CloudflareData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CloudflareConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
