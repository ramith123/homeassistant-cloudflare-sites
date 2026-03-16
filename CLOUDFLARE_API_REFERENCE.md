# Cloudflare API Reference

Developer reference for the Cloudflare API as used by this integration.

## Authentication

### API Token (used by this integration)

```python
from cloudflare import AsyncCloudflare

client = AsyncCloudflare(api_token="your-token-here")
```

Sent as `Authorization: Bearer <token>` header. Create tokens at https://dash.cloudflare.com/profile/api-tokens.

### API Key (legacy, not used)

```python
client = AsyncCloudflare(api_key="key", api_email="email@example.com")
```

## Endpoints Used

### List Zones

Lists all zones the token has access to.

- **REST**: `GET /client/v4/zones`
- **SDK**: `client.zones.list()`

```python
zones = await client.zones.list()
for zone in zones:
    print(zone.id, zone.name)
```

Response fields:
- `id` — Zone identifier (32-char hex string)
- `name` — Domain name (e.g., `example.com`)
- `status` — Zone status (`active`, `pending`, etc.)

### Get Security Level Setting

Retrieves the current security level for a zone.

- **REST**: `GET /client/v4/zones/{zone_id}/settings/security_level`
- **SDK**: `client.zones.settings.get(zone_id=ZONE_ID, setting_id="security_level")`

```python
setting = await client.zones.settings.get(
    zone_id="abc123",
    setting_id="security_level",
)
print(setting.value)  # e.g., "high"
```

### Set Security Level Setting

Updates the security level for a zone.

- **REST**: `PATCH /client/v4/zones/{zone_id}/settings/security_level`
- **SDK**: `client.zones.settings.edit(zone_id=ZONE_ID, setting_id="security_level", body={"value": LEVEL})`

```python
await client.zones.settings.edit(
    zone_id="abc123",
    setting_id="security_level",
    body={"value": "under_attack"},
)
```

## Security Levels

| Level | Description |
|---|---|
| `off` | No security challenges |
| `essentially_off` | Only the most threatening visitors get challenged |
| `low` | Challenges only the most threatening visitors |
| `medium` | Challenges both moderate and most threatening visitors |
| `high` | Challenges all visitors that have exhibited threatening behavior within the last 14 days |
| `under_attack` | "I'm Under Attack" mode — shows a JavaScript challenge to every visitor (5-second interstitial) |

## Rate Limits

Cloudflare API rate limit: **1,200 requests per 5 minutes** per user. With a 30-second poll interval and typical zone counts, this integration stays well within limits.

## Error Handling

The Python SDK raises `cloudflare._exceptions.APIError` for API failures. Common error codes:

| Code | Meaning |
|---|---|
| `6003` | Invalid request headers (bad token format) |
| `9103` | Unknown API token |
| `9109` | Missing required token permissions |
| `7003` | Could not route to zone (invalid zone ID) |

## Python SDK

This integration uses the official [`cloudflare`](https://pypi.org/project/cloudflare/) Python package (v4+), which is auto-generated from Cloudflare's OpenAPI spec.

### Installation

```bash
pip install cloudflare>=4.0.0
```

### Async Usage Pattern

```python
from cloudflare import AsyncCloudflare

async def main():
    client = AsyncCloudflare(api_token="token")

    # List zones
    zones = await client.zones.list()

    # Read setting
    setting = await client.zones.settings.get(
        zone_id=zones[0].id,
        setting_id="security_level",
    )

    # Update setting
    await client.zones.settings.edit(
        zone_id=zones[0].id,
        setting_id="security_level",
        body={"value": "under_attack"},
    )
```

## Home Assistant Integration Patterns

### DataUpdateCoordinator

The integration uses HA's `DataUpdateCoordinator` to poll Cloudflare at a 30-second interval. This centralizes API calls and provides built-in error handling, exponential backoff on failure, and shared data across entities.

### Config Flow

Uses `ConfigFlow` with a single step that validates the API token by attempting to list zones. This catches both authentication errors and permission issues before the entry is created.

### runtime_data

Uses the modern `entry.runtime_data` pattern (HA 2024.4+) to store the coordinator and client, avoiding the legacy `hass.data[DOMAIN]` dictionary approach.
