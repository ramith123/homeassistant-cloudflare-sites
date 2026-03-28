"""Quick local test to verify rulesets API calls work."""

import asyncio
import sys

from cloudflare import AsyncCloudflare


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_rulesets.py <API_TOKEN>")
        sys.exit(1)

    token = sys.argv[1]
    client = AsyncCloudflare(api_token=token)

    # List zones
    zones_response = await client.zones.list()
    zones = zones_response.result
    print(f"Found {len(zones)} zone(s):\n")

    for zone in zones:
        print(f"--- Zone: {zone.name} ({zone.id}) ---")

        # List rulesets
        rulesets_response = await client.rulesets.list(zone_id=zone.id)
        print(f"  rulesets_response type: {type(rulesets_response)}")
        print(f"  has .result: {hasattr(rulesets_response, 'result')}")

        # Try direct iteration
        try:
            rulesets = list(rulesets_response)
            print(f"  direct iteration: {len(rulesets)} ruleset(s)")
        except Exception as e:
            print(f"  direct iteration failed: {e}")

        # Try .result
        try:
            rulesets = rulesets_response.result
            print(f"  .result: {len(rulesets)} ruleset(s)")
        except Exception as e:
            print(f"  .result failed: {e}")

        # Whichever worked, find custom rules phase
        try:
            rulesets = rulesets_response.result if hasattr(rulesets_response, 'result') else list(rulesets_response)
        except Exception:
            rulesets = []

        for rs in rulesets:
            print(f"  Ruleset: id={rs.id}, phase={rs.phase}, name={getattr(rs, 'name', 'N/A')}")
            if rs.phase == "http_request_firewall_custom":
                print(f"    ^ MATCH - fetching full ruleset...")
                full = await client.rulesets.get(ruleset_id=rs.id, zone_id=zone.id)
                print(f"    full ruleset type: {type(full)}")
                print(f"    has .rules: {hasattr(full, 'rules')}")
                if full.rules:
                    print(f"    {len(full.rules)} rule(s):")
                    for rule in full.rules:
                        print(f"      - id={rule.id}, enabled={rule.enabled}, "
                              f"action={rule.action}, desc={rule.description}")
                else:
                    print("    No rules in this ruleset")
        print()


asyncio.run(main())
