"""Dump all unique itemTags from ProfitSage across multiple sites."""

import asyncio
import csv
import os
from collections import defaultdict

import httpx

ENV_PATH = os.path.expanduser("~/.env")
creds = {}
with open(ENV_PATH) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            creds[key.strip()] = val.strip()

BASE = creds.get("API_BASE_URL", "").rstrip("/") + "/PS-Handlers"
USERNAME = creds.get("API_USERNAME", "")
PASSWORD = creds.get("API_PASSWORD", "")

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "profitsage_item_tags.txt")


async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        # Auth
        resp = await client.post(
            f"{BASE}/token",
            data={"grant_type": "password", "username": USERNAME, "password": PASSWORD},
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print("Authenticated.")

        # Get sites
        resp = await client.get(f"{BASE}/api/DataPortalv3/Sites", params={"access_token": token})
        resp.raise_for_status()
        sites = [s["siteTag"] for s in resp.json() if s.get("siteTag") not in ("TMP1", "TMP2")]
        print(f"Found {len(sites)} sites.")

        # Fetch from a few diverse sites to capture all tags
        # (different property types may have different tags)
        sample_sites = sites[:5] + sites[-5:]  # first 5 + last 5
        tags = {}  # itemTag -> {description, accountNumber, statAccount, sample_amt, sample_stat}

        for site in sample_sites:
            print(f"  Fetching site {site}...")
            resp = await client.get(
                f"{BASE}/api/DataPortalv3/DailyExtended",
                params={
                    "access_token": token,
                    "BD": "02/15/2026",
                    "ED": "02/15/2026",
                    "dataSetID": -3,
                    "includeTotals": "Y",
                    "includeZeroes": "Y",
                    "siteTag": site,
                },
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not isinstance(data, list):
                continue

            for row in data:
                tag = row.get("itemTag", "")
                if not tag or tag in tags:
                    continue
                tags[tag] = {
                    "description": row.get("description", ""),
                    "accountNumber": row.get("accountNumber", ""),
                    "statAccount": row.get("statAccount", ""),
                    "sample_amt": row.get("amt", 0),
                    "sample_stat": row.get("stat", 0),
                    "sample_site": site,
                }

        print(f"\nCollected {len(tags)} unique itemTags.")

        # Write output
        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
        with open(OUTPUT, "w") as f:
            f.write(f"ProfitSage Item Tags Reference\n")
            f.write(f"Generated from {len(sample_sites)} sample sites on 2026-02-15\n")
            f.write(f"Total unique tags: {len(tags)}\n")
            f.write(f"{'='*100}\n\n")

            # Group by prefix
            groups = defaultdict(list)
            for tag in sorted(tags.keys()):
                if tag.startswith("I"):
                    groups["I* (Individual GL Line Items)"].append(tag)
                elif tag.startswith("RF"):
                    groups["RF* (Rollup/Formula Tags)"].append(tag)
                elif tag.startswith("TOT"):
                    groups["TOT* (Department/Category Totals)"].append(tag)
                elif tag.startswith("DY"):
                    groups["DY* (Daily Transaction Tags)"].append(tag)
                elif tag.startswith("Q"):
                    groups["Q* (Query/Stat Tags)"].append(tag)
                elif tag.startswith("SEQ"):
                    groups["SEQ* (Sequence Tags)"].append(tag)
                elif tag.startswith("AR"):
                    groups["AR* (Accounts Receivable)"].append(tag)
                elif tag.startswith("CFLW"):
                    groups["CFLW* (Cash Flow)"].append(tag)
                elif tag.startswith("CASH"):
                    groups["CASH* (Cash)"].append(tag)
                elif tag.startswith("CR"):
                    groups["CR* (Credit)"].append(tag)
                elif tag.startswith("COMP"):
                    groups["COMP* (STR Competitive)"].append(tag)
                elif tag.startswith("PA"):
                    groups["PA* (Pace/Pickup)"].append(tag)
                elif tag.startswith("TAX"):
                    groups["TAX* (Tax)"].append(tag)
                elif tag.startswith("LY"):
                    groups["LY* (Laundry)"].append(tag)
                elif tag.startswith("MSNR"):
                    groups["MSNR* (Miscellaneous)"].append(tag)
                elif tag.startswith("ST"):
                    groups["ST* (Statistics)"].append(tag)
                elif tag.startswith("II") or tag.startswith("IJ"):
                    groups["II*/IJ* (Inter-company)"].append(tag)
                else:
                    groups["Other"].append(tag)

            for group_name in sorted(groups.keys()):
                group_tags = groups[group_name]
                f.write(f"--- {group_name} ({len(group_tags)} tags) ---\n\n")
                f.write(f"{'itemTag':<20} {'description':<50} {'accountNumber':<20} {'statAccount':<20}\n")
                f.write(f"{'-'*20} {'-'*50} {'-'*20} {'-'*20}\n")
                for tag in group_tags:
                    info = tags[tag]
                    desc = (info['description'] or '')[:50]
                    acct = info['accountNumber'] or ''
                    stat = info['statAccount'] or ''
                    f.write(f"{tag:<20} {desc:<50} {acct:<20} {stat:<20}\n")
                f.write(f"\n")

        print(f"Written to {OUTPUT}")


asyncio.run(main())
