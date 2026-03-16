# Cloudflare Under Attack - Home Assistant Integration

A HACS-compatible Home Assistant integration that lets you toggle Cloudflare's "Under Attack" mode per-site and monitor current security levels.

## Features

- **Per-zone Under Attack toggle** — one switch per Cloudflare zone
- **Security level sensor** — shows current security level (off, essentially_off, low, medium, high, under_attack)
- **Smart restore** — toggling off restores the previous security level instead of defaulting to a fixed value
- **Auto-discovery** — automatically finds all zones accessible by your API token

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for "Cloudflare Under Attack" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/cloudflare_under_attack` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Cloudflare Under Attack**
3. Enter your Cloudflare API token

### Required API Token Permissions

Create an API token at [Cloudflare Dashboard → API Tokens](https://dash.cloudflare.com/profile/api-tokens) with these permissions:

| Permission | Access |
|---|---|
| **Zone** | Read |
| **Zone Settings** | Read |
| **Zone Settings** | Edit |

Set **Zone Resources** to "All zones" or select specific zones.

## Entities

For each Cloudflare zone, the integration creates:

| Entity | Type | Description |
|---|---|---|
| Under Attack Mode | Switch | Toggle Under Attack mode on/off |
| Security Level | Sensor | Current security level string |

The sensor also exposes `zone_id`, `zone_name`, and `previous_security_level` as state attributes.

## How It Works

- Polls Cloudflare every 30 seconds for current security levels
- Turning the switch **ON** sets the zone to `under_attack`
- Turning the switch **OFF** restores the last known non-under_attack level (defaults to `high` if unknown)
- All entities for a zone are grouped under a single device named after the zone
