#!/usr/bin/env python3
"""Seed the database with fictional demo data for Apex Hospitality Group.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/db python scripts/seed_demo.py
    python scripts/seed_demo.py --database-url postgresql://user:pass@host:5432/db

All hotel names, company names, and data are completely fictional.
"""
import argparse
import calendar
import os
import random
import subprocess
import sys
import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Deterministic randomness so re-runs produce the same data
# ---------------------------------------------------------------------------
RNG = random.Random(42)

# ---------------------------------------------------------------------------
# Fixed UUIDs so the script is idempotent and references are stable
# ---------------------------------------------------------------------------
TENANT_ID = uuid.UUID("a0a0a0a0-0001-4000-8000-000000000001")

PROPERTY_DEFS = [
    {
        "id": uuid.UUID("b0b0b0b0-0001-4000-8000-000000000001"),
        "name": "Summit Ridge Resort",
        "code": "SUMMIT",
        "rooms": 224,
        "tier": "premium",
        "timezone": "America/Denver",
    },
    {
        "id": uuid.UUID("b0b0b0b0-0002-4000-8000-000000000002"),
        "name": "Alpine Vista Lodge",
        "code": "ALPINE",
        "rooms": 156,
        "tier": "upscale",
        "timezone": "America/Denver",
    },
    {
        "id": uuid.UUID("b0b0b0b0-0003-4000-8000-000000000003"),
        "name": "Pinecrest Hotel & Spa",
        "code": "PINE",
        "rooms": 120,
        "tier": "upper_mid",
        "timezone": "America/New_York",
    },
    {
        "id": uuid.UUID("b0b0b0b0-0004-4000-8000-000000000004"),
        "name": "Valley Creek Inn",
        "code": "VALLEY",
        "rooms": 88,
        "tier": "economy",
        "timezone": "America/Chicago",
    },
    {
        "id": uuid.UUID("b0b0b0b0-0005-4000-8000-000000000005"),
        "name": "Cedar Point Suites",
        "code": "CEDAR",
        "rooms": 142,
        "tier": "mid",
        "timezone": "America/New_York",
    },
]

ADMIN_USER_ID = uuid.UUID("c0c0c0c0-0001-4000-8000-000000000001")
MANAGER_USER_ID = uuid.UUID("c0c0c0c0-0002-4000-8000-000000000002")

# ---------------------------------------------------------------------------
# Department types (must match existing schema expectations)
# ---------------------------------------------------------------------------
DEPARTMENT_TYPES = [
    ("rooms", "Rooms"),
    ("fb", "Food & Beverage"),
    ("spa", "Spa"),
    ("golf", "Golf"),
    ("retail", "Retail"),
    ("mountain", "Mountain Operations"),
    ("other", "Other Operated Departments"),
]

# ---------------------------------------------------------------------------
# Line items — full USALI-based chart of accounts
# (code, name, parent_code, dept_type, sort_order, is_summary, data_type)
# ---------------------------------------------------------------------------
LINE_ITEMS = [
    # Top-level summaries
    ("total_revenue", "Total Revenue", None, None, 100, True, "revenue"),
    ("total_dept_expenses", "Total Departmental Expenses", None, None, 200, True, "expense"),
    ("total_gop", "Gross Operating Profit", None, None, 300, True, "revenue"),
    ("total_undist_expenses", "Total Undistributed Expenses", None, None, 400, True, "expense"),
    ("total_fixed_charges", "Total Fixed Charges", None, None, 500, True, "expense"),
    ("net_operating_income", "Net Operating Income", None, None, 600, True, "revenue"),

    # --- Revenue breakdown ---
    ("rooms_revenue", "Rooms Revenue", "total_revenue", "rooms", 110, True, "revenue"),
    ("room_revenue", "Room Revenue", "rooms_revenue", "rooms", 111, False, "revenue"),
    ("transient_revenue", "Transient Revenue", "room_revenue", "rooms", 1111, False, "revenue"),
    ("group_revenue", "Group Revenue", "room_revenue", "rooms", 1112, False, "revenue"),
    ("other_room_revenue", "Other Room Revenue", "rooms_revenue", "rooms", 112, False, "revenue"),

    ("fb_revenue", "Food & Beverage Revenue", "total_revenue", "fb", 120, True, "revenue"),
    ("food_revenue", "Food Revenue", "fb_revenue", "fb", 121, False, "revenue"),
    ("beverage_revenue", "Beverage Revenue", "fb_revenue", "fb", 122, False, "revenue"),
    ("catering_revenue", "Catering Revenue", "fb_revenue", "fb", 123, False, "revenue"),

    ("spa_revenue", "Spa Revenue", "total_revenue", "spa", 130, True, "revenue"),
    ("spa_services_revenue", "Spa Services", "spa_revenue", "spa", 131, False, "revenue"),
    ("spa_retail_revenue", "Spa Retail", "spa_revenue", "spa", 132, False, "revenue"),

    ("golf_revenue", "Golf Revenue", "total_revenue", "golf", 140, True, "revenue"),
    ("golf_greens_revenue", "Greens Fees", "golf_revenue", "golf", 141, False, "revenue"),
    ("golf_cart_revenue", "Cart Rental", "golf_revenue", "golf", 142, False, "revenue"),
    ("golf_pro_shop_revenue", "Pro Shop", "golf_revenue", "golf", 143, False, "revenue"),

    ("mountain_revenue", "Mountain Revenue", "total_revenue", "mountain", 145, True, "revenue"),
    ("mountain_lift_revenue", "Lift Tickets", "mountain_revenue", "mountain", 1451, False, "revenue"),
    ("mountain_rental_revenue", "Equipment Rental", "mountain_revenue", "mountain", 1452, False, "revenue"),

    ("other_revenue", "Other Revenue", "total_revenue", None, 150, True, "revenue"),
    ("parking_revenue", "Parking Revenue", "other_revenue", None, 151, False, "revenue"),
    ("resort_fee_revenue", "Resort Fee Revenue", "other_revenue", None, 152, False, "revenue"),
    ("retail_revenue", "Retail Revenue", "other_revenue", "retail", 153, False, "revenue"),
    ("telecom_revenue", "Telecommunications", "other_revenue", None, 154, False, "revenue"),
    ("misc_revenue", "Miscellaneous Revenue", "other_revenue", None, 155, False, "revenue"),

    # --- Departmental Expenses ---
    ("rooms_expense", "Rooms Expense", "total_dept_expenses", "rooms", 210, True, "expense"),
    ("rooms_labor", "Rooms Labor", "rooms_expense", "rooms", 211, False, "expense"),
    ("rooms_ota_commissions", "OTA Commissions", "rooms_expense", "rooms", 212, False, "expense"),
    ("rooms_supplies", "Rooms Supplies", "rooms_expense", "rooms", 213, False, "expense"),
    ("rooms_other_expense", "Rooms Other Expense", "rooms_expense", "rooms", 214, False, "expense"),

    ("fb_expense", "F&B Expense", "total_dept_expenses", "fb", 220, True, "expense"),
    ("fb_cost_of_sales", "F&B Cost of Sales", "fb_expense", "fb", 221, False, "expense"),
    ("fb_labor", "F&B Labor", "fb_expense", "fb", 222, False, "expense"),
    ("fb_other_expense", "F&B Other Expense", "fb_expense", "fb", 223, False, "expense"),

    ("spa_expense", "Spa Expense", "total_dept_expenses", "spa", 230, True, "expense"),
    ("spa_labor", "Spa Labor", "spa_expense", "spa", 231, False, "expense"),
    ("spa_cost_of_sales", "Spa Cost of Sales", "spa_expense", "spa", 232, False, "expense"),
    ("spa_other_expense", "Spa Other Expense", "spa_expense", "spa", 233, False, "expense"),

    ("golf_expense", "Golf Expense", "total_dept_expenses", "golf", 240, True, "expense"),
    ("golf_labor", "Golf Labor", "golf_expense", "golf", 241, False, "expense"),
    ("golf_maintenance", "Golf Course Maintenance", "golf_expense", "golf", 242, False, "expense"),
    ("golf_other_expense", "Golf Other Expense", "golf_expense", "golf", 243, False, "expense"),

    ("mountain_expense", "Mountain Expense", "total_dept_expenses", "mountain", 245, True, "expense"),
    ("mountain_labor", "Mountain Labor", "mountain_expense", "mountain", 2451, False, "expense"),
    ("mountain_other_expense", "Mountain Other Expense", "mountain_expense", "mountain", 2452, False, "expense"),

    # --- Undistributed Expenses ---
    ("admin_general", "Administrative & General", "total_undist_expenses", None, 410, True, "expense"),
    ("ag_salaries", "A&G Salaries", "admin_general", None, 411, False, "expense"),
    ("ag_professional_fees", "Professional Fees", "admin_general", None, 412, False, "expense"),
    ("ag_other", "A&G Other", "admin_general", None, 413, False, "expense"),

    ("sales_marketing", "Sales & Marketing", "total_undist_expenses", None, 420, True, "expense"),
    ("sm_salaries", "S&M Salaries", "sales_marketing", None, 421, False, "expense"),
    ("sm_advertising", "Advertising", "sales_marketing", None, 422, False, "expense"),
    ("sm_other", "S&M Other", "sales_marketing", None, 423, False, "expense"),

    ("pom", "Property Operations & Maintenance", "total_undist_expenses", None, 430, True, "expense"),
    ("pom_salaries", "POM Salaries", "pom", None, 431, False, "expense"),
    ("pom_repairs", "Repairs & Maintenance", "pom", None, 432, False, "expense"),
    ("pom_utilities", "Utilities", "pom", None, 433, False, "expense"),

    ("energy", "Energy Costs", "total_undist_expenses", None, 440, True, "expense"),
    ("energy_electric", "Electricity", "energy", None, 441, False, "expense"),
    ("energy_gas", "Gas", "energy", None, 442, False, "expense"),
    ("energy_water", "Water & Sewer", "energy", None, 443, False, "expense"),

    # --- Fixed Charges ---
    ("management_fee", "Management Fee", "total_fixed_charges", None, 510, False, "expense"),
    ("property_tax", "Property Taxes", "total_fixed_charges", None, 520, False, "expense"),
    ("insurance", "Insurance", "total_fixed_charges", None, 530, False, "expense"),
    ("rent_lease", "Rent / Ground Lease", "total_fixed_charges", None, 540, False, "expense"),

    # --- Statistical line items ---
    ("rooms_sold", "Rooms Sold", None, "rooms", 810, False, "stat"),
    ("available_rooms", "Available Rooms", None, "rooms", 820, False, "stat"),
    ("occupied_rooms", "Occupied Rooms", None, "rooms", 830, False, "stat"),
    ("covers", "Covers", None, "fb", 840, False, "stat"),
    ("golf_rounds", "Golf Rounds", None, "golf", 850, False, "stat"),
    ("mountain_skier_visits", "Skier Visits", None, "mountain", 860, False, "stat"),
    ("spa_treatments", "Spa Treatments", None, "spa", 870, False, "stat"),

    # --- KPI metrics ---
    ("revpar", "RevPAR", None, "rooms", 700, False, "revenue"),
    ("adr", "ADR", None, "rooms", 710, False, "revenue"),
    ("occupancy_pct", "Occupancy %", None, "rooms", 720, False, "revenue"),
    ("gop_margin", "GOP Margin %", None, None, 730, False, "revenue"),
    ("labor_cost_pct", "Labor Cost %", None, None, 740, False, "expense"),
]

# Line item codes that get daily actuals (non-summary, non-KPI)
DAILY_LINE_ITEM_CODES = [li[0] for li in LINE_ITEMS if not li[5] and li[6] != "stat" and li[0] not in (
    "revpar", "adr", "occupancy_pct", "gop_margin", "labor_cost_pct",
)]

STAT_LINE_ITEM_CODES = [li[0] for li in LINE_ITEMS if li[6] == "stat"]

# ---------------------------------------------------------------------------
# Tier-based configuration for realistic data generation
# All monetary values in CENTS
# ---------------------------------------------------------------------------
TIER_CONFIG = {
    "premium": {
        "base_adr": 32500,       # $325.00
        "occ_base": 0.72,
        "weekend_bump": 0.15,
        "winter_bump": 0.10,     # mountain resort
        "food_pct": 0.25,
        "bev_pct": 0.08,
        "spa_pct": 0.06,
        "golf_pct": 0.05,
        "mountain_pct": 0.08,
    },
    "upscale": {
        "base_adr": 24500,       # $245.00
        "occ_base": 0.68,
        "weekend_bump": 0.12,
        "winter_bump": 0.08,
        "food_pct": 0.22,
        "bev_pct": 0.07,
        "spa_pct": 0.04,
        "golf_pct": 0.04,
        "mountain_pct": 0.06,
    },
    "upper_mid": {
        "base_adr": 18900,       # $189.00
        "occ_base": 0.65,
        "weekend_bump": 0.10,
        "winter_bump": 0.03,
        "food_pct": 0.18,
        "bev_pct": 0.06,
        "spa_pct": 0.05,
        "golf_pct": 0.02,
        "mountain_pct": 0.0,
    },
    "mid": {
        "base_adr": 15500,       # $155.00
        "occ_base": 0.62,
        "weekend_bump": 0.10,
        "winter_bump": 0.02,
        "food_pct": 0.15,
        "bev_pct": 0.05,
        "spa_pct": 0.02,
        "golf_pct": 0.01,
        "mountain_pct": 0.0,
    },
    "economy": {
        "base_adr": 10900,       # $109.00
        "occ_base": 0.60,
        "weekend_bump": 0.08,
        "winter_bump": 0.0,
        "food_pct": 0.12,
        "bev_pct": 0.04,
        "spa_pct": 0.0,
        "golf_pct": 0.0,
        "mountain_pct": 0.0,
    },
}

# Expense ratios as fraction of room_revenue for the property
EXPENSE_RATIOS = {
    "rooms_labor": 0.18,
    "rooms_ota_commissions": 0.06,
    "rooms_supplies": 0.02,
    "rooms_other_expense": 0.01,
    "fb_cost_of_sales": 0.30,       # of F&B revenue
    "fb_labor": 0.35,               # of F&B revenue
    "fb_other_expense": 0.05,       # of F&B revenue
    "spa_labor": 0.40,              # of spa revenue
    "spa_cost_of_sales": 0.15,      # of spa revenue
    "spa_other_expense": 0.05,      # of spa revenue
    "golf_labor": 0.35,             # of golf revenue
    "golf_maintenance": 0.20,       # of golf revenue
    "golf_other_expense": 0.05,     # of golf revenue
    "mountain_labor": 0.30,         # of mountain revenue
    "mountain_other_expense": 0.10, # of mountain revenue
    "ag_salaries": 0.04,            # of total revenue
    "ag_professional_fees": 0.01,
    "ag_other": 0.005,
    "sm_salaries": 0.025,
    "sm_advertising": 0.015,
    "sm_other": 0.005,
    "pom_salaries": 0.02,
    "pom_repairs": 0.015,
    "pom_utilities": 0.02,
    "energy_electric": 0.025,
    "energy_gas": 0.01,
    "energy_water": 0.008,
    "management_fee": 0.03,
    "property_tax": 0.025,
    "insurance": 0.012,
    "rent_lease": 0.04,
}


def _jitter(value: int, pct: float = 0.08) -> int:
    """Add random jitter to a value (default ±8%)."""
    factor = 1.0 + RNG.uniform(-pct, pct)
    return max(0, int(value * factor))


def generate_daily_actuals(prop: dict, line_item_ids: dict) -> list[dict]:
    """Generate 90 days of daily actuals for a single property (Jan 1 - Mar 31, 2026)."""
    tier = TIER_CONFIG[prop["tier"]]
    rooms = prop["rooms"]
    rows = []

    start = date(2026, 1, 1)
    end = date(2026, 3, 31)
    d = start

    while d <= end:
        day_of_week = d.weekday()  # 0=Mon, 6=Sun
        is_weekend = day_of_week >= 4  # Fri-Sun
        month = d.month

        # --- Occupancy ---
        occ = tier["occ_base"]
        if is_weekend:
            occ += tier["weekend_bump"]
        # Winter bump for Jan-Feb
        if month <= 2:
            occ += tier["winter_bump"]
        # March slight dip for shoulder season
        if month == 3:
            occ -= 0.03
        occ = min(0.98, max(0.35, occ + RNG.uniform(-0.06, 0.06)))

        occupied = int(rooms * occ)
        adr = _jitter(tier["base_adr"])
        # Weekend ADR premium
        if is_weekend:
            adr = int(adr * 1.12)
        # Winter premium for mountain properties
        if month <= 2 and tier["winter_bump"] > 0:
            adr = int(adr * 1.08)

        total_room_rev = occupied * adr
        # Split room revenue into transient / group
        group_pct = RNG.uniform(0.25, 0.45)
        transient_rev = int(total_room_rev * (1 - group_pct))
        group_rev = total_room_rev - transient_rev
        other_room_rev = _jitter(int(total_room_rev * 0.03))

        food_rev = _jitter(int(total_room_rev * tier["food_pct"]))
        bev_rev = _jitter(int(total_room_rev * tier["bev_pct"]))
        catering_rev = _jitter(int(total_room_rev * RNG.uniform(0.03, 0.08)))

        spa_svc_rev = _jitter(int(total_room_rev * tier["spa_pct"])) if tier["spa_pct"] else 0
        spa_ret_rev = _jitter(int(spa_svc_rev * 0.15)) if spa_svc_rev else 0

        golf_greens = _jitter(int(total_room_rev * tier["golf_pct"])) if tier["golf_pct"] else 0
        golf_cart = _jitter(int(golf_greens * 0.35)) if golf_greens else 0
        golf_pro = _jitter(int(golf_greens * 0.20)) if golf_greens else 0

        mtn_lift = _jitter(int(total_room_rev * tier["mountain_pct"])) if tier["mountain_pct"] else 0
        mtn_rental = _jitter(int(mtn_lift * 0.25)) if mtn_lift else 0

        parking_rev = _jitter(int(occupied * 1500))  # ~$15/room/night
        resort_fee = _jitter(int(occupied * 2500))    # ~$25/room/night
        retail_rev = _jitter(int(total_room_rev * 0.02))
        telecom_rev = _jitter(int(occupied * 200))
        misc_rev = _jitter(int(total_room_rev * 0.005))

        # Total revenue for expense calculations
        total_rev = (total_room_rev + other_room_rev + food_rev + bev_rev +
                     catering_rev + spa_svc_rev + spa_ret_rev + golf_greens +
                     golf_cart + golf_pro + mtn_lift + mtn_rental +
                     parking_rev + resort_fee + retail_rev + telecom_rev + misc_rev)
        fb_rev = food_rev + bev_rev + catering_rev
        spa_rev = spa_svc_rev + spa_ret_rev
        golf_rev = golf_greens + golf_cart + golf_pro
        mtn_rev = mtn_lift + mtn_rental

        revenue_map = {
            "transient_revenue": transient_rev,
            "group_revenue": group_rev,
            "other_room_revenue": other_room_rev,
            "food_revenue": food_rev,
            "beverage_revenue": bev_rev,
            "catering_revenue": catering_rev,
            "spa_services_revenue": spa_svc_rev,
            "spa_retail_revenue": spa_ret_rev,
            "golf_greens_revenue": golf_greens,
            "golf_cart_revenue": golf_cart,
            "golf_pro_shop_revenue": golf_pro,
            "mountain_lift_revenue": mtn_lift,
            "mountain_rental_revenue": mtn_rental,
            "parking_revenue": parking_rev,
            "resort_fee_revenue": resort_fee,
            "retail_revenue": retail_rev,
            "telecom_revenue": telecom_rev,
            "misc_revenue": misc_rev,
        }

        expense_map = {
            "rooms_labor": _jitter(int(total_room_rev * EXPENSE_RATIOS["rooms_labor"])),
            "rooms_ota_commissions": _jitter(int(total_room_rev * EXPENSE_RATIOS["rooms_ota_commissions"])),
            "rooms_supplies": _jitter(int(total_room_rev * EXPENSE_RATIOS["rooms_supplies"])),
            "rooms_other_expense": _jitter(int(total_room_rev * EXPENSE_RATIOS["rooms_other_expense"])),
            "fb_cost_of_sales": _jitter(int(fb_rev * EXPENSE_RATIOS["fb_cost_of_sales"])),
            "fb_labor": _jitter(int(fb_rev * EXPENSE_RATIOS["fb_labor"])),
            "fb_other_expense": _jitter(int(fb_rev * EXPENSE_RATIOS["fb_other_expense"])),
            "spa_labor": _jitter(int(spa_rev * EXPENSE_RATIOS["spa_labor"])) if spa_rev else 0,
            "spa_cost_of_sales": _jitter(int(spa_rev * EXPENSE_RATIOS["spa_cost_of_sales"])) if spa_rev else 0,
            "spa_other_expense": _jitter(int(spa_rev * EXPENSE_RATIOS["spa_other_expense"])) if spa_rev else 0,
            "golf_labor": _jitter(int(golf_rev * EXPENSE_RATIOS["golf_labor"])) if golf_rev else 0,
            "golf_maintenance": _jitter(int(golf_rev * EXPENSE_RATIOS["golf_maintenance"])) if golf_rev else 0,
            "golf_other_expense": _jitter(int(golf_rev * EXPENSE_RATIOS["golf_other_expense"])) if golf_rev else 0,
            "mountain_labor": _jitter(int(mtn_rev * EXPENSE_RATIOS["mountain_labor"])) if mtn_rev else 0,
            "mountain_other_expense": _jitter(int(mtn_rev * EXPENSE_RATIOS["mountain_other_expense"])) if mtn_rev else 0,
            "ag_salaries": _jitter(int(total_rev * EXPENSE_RATIOS["ag_salaries"])),
            "ag_professional_fees": _jitter(int(total_rev * EXPENSE_RATIOS["ag_professional_fees"])),
            "ag_other": _jitter(int(total_rev * EXPENSE_RATIOS["ag_other"])),
            "sm_salaries": _jitter(int(total_rev * EXPENSE_RATIOS["sm_salaries"])),
            "sm_advertising": _jitter(int(total_rev * EXPENSE_RATIOS["sm_advertising"])),
            "sm_other": _jitter(int(total_rev * EXPENSE_RATIOS["sm_other"])),
            "pom_salaries": _jitter(int(total_rev * EXPENSE_RATIOS["pom_salaries"])),
            "pom_repairs": _jitter(int(total_rev * EXPENSE_RATIOS["pom_repairs"])),
            "pom_utilities": _jitter(int(total_rev * EXPENSE_RATIOS["pom_utilities"])),
            "energy_electric": _jitter(int(total_rev * EXPENSE_RATIOS["energy_electric"])),
            "energy_gas": _jitter(int(total_rev * EXPENSE_RATIOS["energy_gas"])),
            "energy_water": _jitter(int(total_rev * EXPENSE_RATIOS["energy_water"])),
            "management_fee": _jitter(int(total_rev * EXPENSE_RATIOS["management_fee"])),
            "property_tax": _jitter(int(total_rev * EXPENSE_RATIOS["property_tax"]), pct=0.02),
            "insurance": _jitter(int(total_rev * EXPENSE_RATIOS["insurance"]), pct=0.02),
            "rent_lease": _jitter(int(total_rev * EXPENSE_RATIOS["rent_lease"]), pct=0.01),
        }

        stat_map = {
            "rooms_sold": occupied,
            "available_rooms": rooms,
            "occupied_rooms": occupied,
            "covers": int(occupied * RNG.uniform(1.2, 2.0)),
            "golf_rounds": int(occupied * RNG.uniform(0.1, 0.3)) if golf_greens else 0,
            "mountain_skier_visits": int(occupied * RNG.uniform(0.3, 0.8)) if mtn_lift else 0,
            "spa_treatments": int(occupied * RNG.uniform(0.05, 0.15)) if spa_svc_rev else 0,
        }

        # Build row dicts
        all_items = {}
        all_items.update(revenue_map)
        all_items.update(expense_map)
        all_items.update(stat_map)

        for code, value in all_items.items():
            if code not in line_item_ids:
                continue
            if value == 0 and code in stat_map:
                continue  # skip zero stats
            rows.append({
                "tenant_id": str(TENANT_ID),
                "property_id": str(prop["id"]),
                "date": d,
                "line_item_id": str(line_item_ids[code]),
                "value": value,
            })

        d = date.fromordinal(d.toordinal() + 1)

    return rows


def generate_monthly_budgets(prop: dict, line_item_ids: dict) -> list[dict]:
    """Generate monthly budgets for all 12 months of 2026.

    Budgets are derived from what actuals *would* be, with 95-105% variance.
    """
    tier = TIER_CONFIG[prop["tier"]]
    rooms = prop["rooms"]
    rows = []

    for month in range(1, 13):
        days_in_month = calendar.monthrange(2026, month)[1]

        # Estimate monthly totals
        occ = tier["occ_base"]
        if month <= 2:
            occ += tier["winter_bump"]
        if month in (6, 7, 8):
            occ += 0.05  # summer bump
        if month in (4, 11):
            occ -= 0.05  # shoulder season
        occ = min(0.95, max(0.45, occ))

        avg_occupied = int(rooms * occ)
        monthly_occupied = avg_occupied * days_in_month
        adr = tier["base_adr"]
        if month <= 2 and tier["winter_bump"] > 0:
            adr = int(adr * 1.08)

        total_room_rev = monthly_occupied * adr
        group_pct = 0.35
        transient_rev = int(total_room_rev * (1 - group_pct))
        group_rev = total_room_rev - transient_rev
        other_room_rev = int(total_room_rev * 0.03)

        food_rev = int(total_room_rev * tier["food_pct"])
        bev_rev = int(total_room_rev * tier["bev_pct"])
        catering_rev = int(total_room_rev * 0.05)

        spa_svc_rev = int(total_room_rev * tier["spa_pct"]) if tier["spa_pct"] else 0
        spa_ret_rev = int(spa_svc_rev * 0.15) if spa_svc_rev else 0

        golf_greens = int(total_room_rev * tier["golf_pct"]) if tier["golf_pct"] else 0
        golf_cart = int(golf_greens * 0.35) if golf_greens else 0
        golf_pro = int(golf_greens * 0.20) if golf_greens else 0

        mtn_lift = int(total_room_rev * tier["mountain_pct"]) if tier["mountain_pct"] else 0
        mtn_rental = int(mtn_lift * 0.25) if mtn_lift else 0

        parking_rev = int(monthly_occupied * 1500)
        resort_fee = int(monthly_occupied * 2500)
        retail_rev = int(total_room_rev * 0.02)
        telecom_rev = int(monthly_occupied * 200)
        misc_rev = int(total_room_rev * 0.005)

        total_rev = (total_room_rev + other_room_rev + food_rev + bev_rev +
                     catering_rev + spa_svc_rev + spa_ret_rev + golf_greens +
                     golf_cart + golf_pro + mtn_lift + mtn_rental +
                     parking_rev + resort_fee + retail_rev + telecom_rev + misc_rev)
        fb_rev = food_rev + bev_rev + catering_rev
        spa_rev = spa_svc_rev + spa_ret_rev
        golf_rev = golf_greens + golf_cart + golf_pro
        mtn_rev = mtn_lift + mtn_rental

        budget_items = {
            "transient_revenue": transient_rev,
            "group_revenue": group_rev,
            "other_room_revenue": other_room_rev,
            "food_revenue": food_rev,
            "beverage_revenue": bev_rev,
            "catering_revenue": catering_rev,
            "spa_services_revenue": spa_svc_rev,
            "spa_retail_revenue": spa_ret_rev,
            "golf_greens_revenue": golf_greens,
            "golf_cart_revenue": golf_cart,
            "golf_pro_shop_revenue": golf_pro,
            "mountain_lift_revenue": mtn_lift,
            "mountain_rental_revenue": mtn_rental,
            "parking_revenue": parking_rev,
            "resort_fee_revenue": resort_fee,
            "retail_revenue": retail_rev,
            "telecom_revenue": telecom_rev,
            "misc_revenue": misc_rev,
            # Expenses
            "rooms_labor": int(total_room_rev * EXPENSE_RATIOS["rooms_labor"]),
            "rooms_ota_commissions": int(total_room_rev * EXPENSE_RATIOS["rooms_ota_commissions"]),
            "rooms_supplies": int(total_room_rev * EXPENSE_RATIOS["rooms_supplies"]),
            "rooms_other_expense": int(total_room_rev * EXPENSE_RATIOS["rooms_other_expense"]),
            "fb_cost_of_sales": int(fb_rev * EXPENSE_RATIOS["fb_cost_of_sales"]),
            "fb_labor": int(fb_rev * EXPENSE_RATIOS["fb_labor"]),
            "fb_other_expense": int(fb_rev * EXPENSE_RATIOS["fb_other_expense"]),
            "spa_labor": int(spa_rev * EXPENSE_RATIOS["spa_labor"]) if spa_rev else 0,
            "spa_cost_of_sales": int(spa_rev * EXPENSE_RATIOS["spa_cost_of_sales"]) if spa_rev else 0,
            "spa_other_expense": int(spa_rev * EXPENSE_RATIOS["spa_other_expense"]) if spa_rev else 0,
            "golf_labor": int(golf_rev * EXPENSE_RATIOS["golf_labor"]) if golf_rev else 0,
            "golf_maintenance": int(golf_rev * EXPENSE_RATIOS["golf_maintenance"]) if golf_rev else 0,
            "golf_other_expense": int(golf_rev * EXPENSE_RATIOS["golf_other_expense"]) if golf_rev else 0,
            "mountain_labor": int(mtn_rev * EXPENSE_RATIOS["mountain_labor"]) if mtn_rev else 0,
            "mountain_other_expense": int(mtn_rev * EXPENSE_RATIOS["mountain_other_expense"]) if mtn_rev else 0,
            "ag_salaries": int(total_rev * EXPENSE_RATIOS["ag_salaries"]),
            "ag_professional_fees": int(total_rev * EXPENSE_RATIOS["ag_professional_fees"]),
            "ag_other": int(total_rev * EXPENSE_RATIOS["ag_other"]),
            "sm_salaries": int(total_rev * EXPENSE_RATIOS["sm_salaries"]),
            "sm_advertising": int(total_rev * EXPENSE_RATIOS["sm_advertising"]),
            "sm_other": int(total_rev * EXPENSE_RATIOS["sm_other"]),
            "pom_salaries": int(total_rev * EXPENSE_RATIOS["pom_salaries"]),
            "pom_repairs": int(total_rev * EXPENSE_RATIOS["pom_repairs"]),
            "pom_utilities": int(total_rev * EXPENSE_RATIOS["pom_utilities"]),
            "energy_electric": int(total_rev * EXPENSE_RATIOS["energy_electric"]),
            "energy_gas": int(total_rev * EXPENSE_RATIOS["energy_gas"]),
            "energy_water": int(total_rev * EXPENSE_RATIOS["energy_water"]),
            "management_fee": int(total_rev * EXPENSE_RATIOS["management_fee"]),
            "property_tax": int(total_rev * EXPENSE_RATIOS["property_tax"]),
            "insurance": int(total_rev * EXPENSE_RATIOS["insurance"]),
            "rent_lease": int(total_rev * EXPENSE_RATIOS["rent_lease"]),
        }

        # Stats as monthly totals
        stat_items = {
            "rooms_sold": monthly_occupied,
            "available_rooms": rooms * days_in_month,
            "occupied_rooms": monthly_occupied,
            "covers": int(monthly_occupied * 1.5),
            "golf_rounds": int(monthly_occupied * 0.2) if golf_greens else 0,
            "mountain_skier_visits": int(monthly_occupied * 0.5) if mtn_lift else 0,
            "spa_treatments": int(monthly_occupied * 0.1) if spa_svc_rev else 0,
        }

        budget_items.update(stat_items)

        for code, value in budget_items.items():
            if code not in line_item_ids:
                continue
            if value == 0:
                continue
            # Apply budget variance: 95-105% of "ideal" value
            budget_val = int(value * RNG.uniform(0.95, 1.05))
            rows.append({
                "tenant_id": str(TENANT_ID),
                "property_id": str(prop["id"]),
                "year": 2026,
                "month": month,
                "line_item_id": str(line_item_ids[code]),
                "value": budget_val,
            })

    return rows


def run_migrations(db_url: str) -> None:
    """Run alembic upgrade head."""
    print("[1/6] Running Alembic migrations...")
    env = os.environ.copy()
    # Alembic env.py reads DATABASE_URL via app.config.Settings
    # Ensure the sync URL is available
    sync_url = db_url.replace("+asyncpg", "").replace("asyncpg://", "postgresql://")
    if not sync_url.startswith("postgresql://"):
        sync_url = "postgresql://" + sync_url.split("://", 1)[-1]
    env["DATABASE_URL"] = sync_url.replace("postgresql://", "postgresql+asyncpg://")
    env["DATABASE_URL_SYNC"] = sync_url

    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  Migration STDERR: {result.stderr}")
        print(f"  Migration STDOUT: {result.stdout}")
        raise RuntimeError("Alembic migrations failed")
    print("  Migrations complete.")


def seed(db_url: str) -> None:
    """Main seed function."""
    # Normalize to sync postgresql URL
    sync_url = db_url.replace("+asyncpg", "").replace("asyncpg://", "postgresql://")
    if not sync_url.startswith("postgresql://"):
        sync_url = "postgresql://" + sync_url.split("://", 1)[-1]

    engine = create_engine(sync_url)

    with engine.begin() as conn:
        # --- Idempotency check ---
        existing = conn.execute(
            text("SELECT id FROM tenants WHERE id = :tid"),
            {"tid": str(TENANT_ID)},
        ).fetchone()
        if existing:
            print("  Seed data already exists (tenant found). Skipping.")
            return

        # --- Tenant ---
        print("[2/6] Creating tenant: Apex Hospitality Group...")
        conn.execute(text("""
            INSERT INTO tenants (id, name, slug, domain)
            VALUES (:id, :name, :slug, :domain)
        """), {
            "id": str(TENANT_ID),
            "name": "Apex Hospitality Group",
            "slug": "apex-hospitality",
            "domain": "apex.localhost",
        })

        # Set RLS context
        conn.execute(text(f"SET LOCAL app.current_tenant_id = '{TENANT_ID}'"))

        # --- Users ---
        print("[3/6] Creating users...")
        conn.execute(text("""
            INSERT INTO users (id, tenant_id, clerk_id, email, name, role)
            VALUES (:id, :tid, :clerk_id, :email, :name, :role)
        """), {
            "id": str(ADMIN_USER_ID),
            "tid": str(TENANT_ID),
            "clerk_id": "clerk_demo_admin",
            "email": "admin@apexhospitality.demo",
            "name": "Demo Admin",
            "role": "admin",
        })
        conn.execute(text("""
            INSERT INTO users (id, tenant_id, clerk_id, email, name, role)
            VALUES (:id, :tid, :clerk_id, :email, :name, :role)
        """), {
            "id": str(MANAGER_USER_ID),
            "tid": str(TENANT_ID),
            "clerk_id": "clerk_demo_manager",
            "email": "jmiller@apexhospitality.demo",
            "name": "Jason Miller",
            "role": "manager",
        })

        # --- Properties & Departments ---
        print("[4/6] Creating properties and departments...")
        for prop in PROPERTY_DEFS:
            conn.execute(text("""
                INSERT INTO properties (id, tenant_id, name, code, timezone, available_rooms)
                VALUES (:id, :tid, :name, :code, :tz, :rooms)
            """), {
                "id": str(prop["id"]),
                "tid": str(TENANT_ID),
                "name": prop["name"],
                "code": prop["code"],
                "tz": prop["timezone"],
                "rooms": prop["rooms"],
            })

            for dtype, dname in DEPARTMENT_TYPES:
                conn.execute(text("""
                    INSERT INTO departments (tenant_id, property_id, type, name)
                    VALUES (:tid, :pid, :dtype, :dname)
                """), {
                    "tid": str(TENANT_ID),
                    "pid": str(prop["id"]),
                    "dtype": dtype,
                    "dname": dname,
                })

            print(f"    {prop['name']} ({prop['code']}) — {prop['rooms']} rooms")

        # Assign manager to Summit Ridge
        conn.execute(text("""
            INSERT INTO user_properties (user_id, property_id, tenant_id)
            VALUES (:uid, :pid, :tid)
        """), {
            "uid": str(MANAGER_USER_ID),
            "pid": str(PROPERTY_DEFS[0]["id"]),
            "tid": str(TENANT_ID),
        })
        # Assign admin to all properties
        for prop in PROPERTY_DEFS:
            conn.execute(text("""
                INSERT INTO user_properties (user_id, property_id, tenant_id)
                VALUES (:uid, :pid, :tid)
            """), {
                "uid": str(ADMIN_USER_ID),
                "pid": str(prop["id"]),
                "tid": str(TENANT_ID),
            })

        # --- Line Items ---
        print("[4/6] Creating chart of accounts (line items)...")
        # Insert line items in order (parents before children)
        line_item_ids: dict[str, str] = {}
        for code, name, parent_code, dept_type, sort_order, is_summary, data_type in LINE_ITEMS:
            li_id = str(uuid.uuid5(TENANT_ID, code))
            line_item_ids[code] = li_id

            parent_id = line_item_ids.get(parent_code) if parent_code else None

            conn.execute(text("""
                INSERT INTO line_items (id, tenant_id, code, name, parent_id, department_type,
                                        sort_order, is_summary, data_type)
                VALUES (:id, :tid, :code, :name, :parent_id, :dept_type,
                        :sort_order, :is_summary, :data_type)
            """), {
                "id": li_id,
                "tid": str(TENANT_ID),
                "code": code,
                "name": name,
                "parent_id": parent_id,
                "dept_type": dept_type,
                "sort_order": sort_order,
                "is_summary": is_summary,
                "data_type": data_type,
            })

        print(f"    {len(LINE_ITEMS)} line items created.")

        # --- Daily Actuals ---
        print("[5/6] Generating daily actuals (90 days × 5 properties)...")
        total_actuals = 0
        for prop in PROPERTY_DEFS:
            actuals = generate_daily_actuals(prop, line_item_ids)
            if actuals:
                conn.execute(
                    text("""
                        INSERT INTO daily_actuals (tenant_id, property_id, date, line_item_id, value)
                        VALUES (:tenant_id, :property_id, :date, :line_item_id, :value)
                    """),
                    actuals,
                )
                total_actuals += len(actuals)
                print(f"    {prop['name']}: {len(actuals)} daily records")

        print(f"    Total: {total_actuals} daily actual records.")

        # --- Budgets ---
        print("[6/6] Generating monthly budgets (12 months × 5 properties)...")
        total_budgets = 0
        for prop in PROPERTY_DEFS:
            budgets = generate_monthly_budgets(prop, line_item_ids)
            if budgets:
                conn.execute(
                    text("""
                        INSERT INTO budgets (tenant_id, property_id, year, month, line_item_id, value)
                        VALUES (:tenant_id, :property_id, :year, :month, :line_item_id, :value)
                    """),
                    budgets,
                )
                total_budgets += len(budgets)
                print(f"    {prop['name']}: {len(budgets)} budget records")

        print(f"    Total: {total_budgets} budget records.")

    engine.dispose()
    print("\nSeed complete!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for Apex Hospitality Group")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="PostgreSQL connection URL (or set DATABASE_URL env var)",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running Alembic migrations",
    )
    args = parser.parse_args()

    db_url = args.database_url
    if not db_url:
        print("ERROR: No database URL provided.")
        print("  Set DATABASE_URL env var or pass --database-url")
        sys.exit(1)

    if not args.skip_migrations:
        run_migrations(db_url)

    seed(db_url)


if __name__ == "__main__":
    main()
