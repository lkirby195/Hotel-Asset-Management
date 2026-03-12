"""Seed data - test tenant, property, USALI chart of accounts, admin user

Revision ID: 004
Revises: 003
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for seed data to make references easy
TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROPERTY_ID = "00000000-0000-0000-0000-000000000010"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000100"


def upgrade() -> None:
    # Temporarily set tenant context for RLS
    op.execute(f"SET LOCAL app.current_tenant_id = '{TENANT_ID}'")

    # --- Tenant ---
    op.execute(f"""
        INSERT INTO tenants (id, name, slug, domain)
        VALUES ('{TENANT_ID}', 'Mission Hill Hospitality', 'mission-hill', 'missionhill.localhost')
    """)

    # --- Admin User ---
    op.execute(f"""
        INSERT INTO users (id, tenant_id, clerk_id, email, name, role)
        VALUES (
            '{ADMIN_USER_ID}', '{TENANT_ID}',
            'clerk_seed_admin', 'admin@missionhill.com', 'System Admin', 'admin'
        )
    """)

    # --- Sample Property ---
    op.execute(f"""
        INSERT INTO properties (id, tenant_id, name, code, timezone)
        VALUES ('{PROPERTY_ID}', '{TENANT_ID}', 'Mountain Grand Lodge', 'MGL', 'America/Denver')
    """)

    # --- Departments for sample property ---
    dept_types = [
        ("rooms", "Rooms"),
        ("fb", "Food & Beverage"),
        ("spa", "Spa"),
        ("golf", "Golf"),
        ("retail", "Retail"),
        ("mountain", "Mountain Operations"),
        ("other", "Other Operated Departments"),
    ]
    for dtype, dname in dept_types:
        op.execute(f"""
            INSERT INTO departments (property_id, tenant_id, type, name)
            VALUES ('{PROPERTY_ID}', '{TENANT_ID}', '{dtype}', '{dname}')
        """)

    # --- Hierarchical Line Items (USALI-based) ---
    # Format: (code, name, parent_code_or_null, dept_type, sort_order, is_summary, data_type)
    line_items = [
        # Top-level summaries
        ("total_revenue", "Total Revenue", None, None, 100, True, "revenue"),
        ("total_dept_expenses", "Total Departmental Expenses", None, None, 200, True, "expense"),
        ("total_gop", "Gross Operating Profit", None, None, 300, True, "revenue"),
        ("total_undist_expenses", "Total Undistributed Expenses", None, None, 400, True, "expense"),
        ("total_fixed_charges", "Total Fixed Charges", None, None, 500, True, "expense"),
        ("net_operating_income", "Net Operating Income", None, None, 600, True, "revenue"),

        # Revenue breakdown
        ("rooms_revenue", "Rooms Revenue", "total_revenue", "rooms", 110, True, "revenue"),
        ("room_revenue", "Room Revenue", "rooms_revenue", "rooms", 111, False, "revenue"),
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

        ("other_revenue", "Other Revenue", "total_revenue", None, 150, True, "revenue"),
        ("parking_revenue", "Parking Revenue", "other_revenue", None, 151, False, "revenue"),
        ("telecom_revenue", "Telecommunications", "other_revenue", None, 152, False, "revenue"),
        ("misc_revenue", "Miscellaneous Revenue", "other_revenue", None, 153, False, "revenue"),

        # Departmental Expenses
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

        # Undistributed Expenses
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

        # Fixed Charges
        ("management_fee", "Management Fee", "total_fixed_charges", None, 510, False, "expense"),
        ("property_tax", "Property Taxes", "total_fixed_charges", None, 520, False, "expense"),
        ("insurance", "Insurance", "total_fixed_charges", None, 530, False, "expense"),
        ("rent_lease", "Rent / Ground Lease", "total_fixed_charges", None, 540, False, "expense"),

        # KPI metrics (calculated, stored as per_unit_value)
        ("revpar", "RevPAR", None, "rooms", 700, False, "revenue"),
        ("adr", "ADR", None, "rooms", 710, False, "revenue"),
        ("occupancy_pct", "Occupancy %", None, "rooms", 720, False, "revenue"),
        ("gop_margin", "GOP Margin %", None, None, 730, False, "revenue"),
        ("labor_cost_pct", "Labor Cost %", None, None, 740, False, "expense"),
    ]

    for code, name, parent_code, dept_type, sort_order, is_summary, data_type in line_items:
        parent_clause = "NULL"
        if parent_code:
            parent_clause = f"(SELECT id FROM line_items WHERE tenant_id = '{TENANT_ID}' AND code = '{parent_code}')"

        dept_clause = f"'{dept_type}'" if dept_type else "NULL"

        op.execute(f"""
            INSERT INTO line_items (tenant_id, code, name, parent_id, department_type, sort_order, is_summary, data_type)
            VALUES (
                '{TENANT_ID}', '{code}', '{name}',
                {parent_clause}, {dept_clause},
                {sort_order}, {str(is_summary).lower()}, '{data_type}'
            )
        """)

    # --- Assign admin to the sample property ---
    op.execute(f"""
        INSERT INTO user_properties (user_id, property_id, tenant_id)
        VALUES ('{ADMIN_USER_ID}', '{PROPERTY_ID}', '{TENANT_ID}')
    """)


def downgrade() -> None:
    op.execute(f"SET LOCAL app.current_tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM user_properties WHERE tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM departments WHERE tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM line_items WHERE tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM properties WHERE tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM users WHERE tenant_id = '{TENANT_ID}'")
    op.execute(f"DELETE FROM tenants WHERE id = '{TENANT_ID}'")
