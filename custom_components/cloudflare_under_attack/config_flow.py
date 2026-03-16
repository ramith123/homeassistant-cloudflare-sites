"""Config flow for Cloudflare Under Attack integration."""

from __future__ import annotations

import logging
from typing import Any

from cloudflare import AsyncCloudflare
from cloudflare._exceptions import APIError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_API_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
    }
)


class CloudflareUnderAttackConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloudflare Under Attack."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input[CONF_API_TOKEN]

            # Use first 16 chars of token as unique ID to prevent duplicates
            await self.async_set_unique_id(token[:16])
            self._abort_if_unique_id_configured()

            try:
                client = AsyncCloudflare(api_token=token)
                zones_response = await client.zones.list()
                zones = list(zones_response.result)
            except (APIError, Exception) as err:
                _LOGGER.error("Failed to connect to Cloudflare: %s", err)
                errors["base"] = "cannot_connect"
            else:
                if not zones:
                    errors["base"] = "no_zones"
                else:
                    return self.async_create_entry(
                        title="Cloudflare Under Attack",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
