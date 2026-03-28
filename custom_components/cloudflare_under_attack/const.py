"""Constants for the Cloudflare Under Attack integration."""

from datetime import timedelta

DOMAIN = "cloudflare_under_attack"

CONF_API_TOKEN = "api_token"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

SECURITY_LEVEL_UNDER_ATTACK = "under_attack"
DEFAULT_SECURITY_LEVEL = "high"

WAF_CUSTOM_RULES_PHASE = "http_request_firewall_custom"

SECURITY_LEVELS = [
    "off",
    "essentially_off",
    "low",
    "medium",
    "high",
    "under_attack",
]
