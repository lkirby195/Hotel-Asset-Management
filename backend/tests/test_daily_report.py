"""Tests for the daily report API and service."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.daily_report import DailyReportResponse, DailyReportSection, DualPanelRow
from app.services.daily_report_service import DailyReportService
from tests.conftest import PROPERTY_ID


# ── Service unit tests ────────────────────────────────────────────


class TestDailyReportService:

    @pytest.fixture
    def service(self):
        return DailyReportService()

    @pytest.fixture
    def mock_db(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    def _stub_db_rows(self, mock_db, data: dict[str, float]):
        """Configure mock_db.execute to return rows for each code/value."""
        rows = [MagicMock(code=code, value=value) for code, value in data.items()]
        result = MagicMock()
        result.fetchall.return_value = rows
        mock_db.execute.return_value = result

    def _stub_db_empty(self, mock_db):
        result = MagicMock()
        result.fetchall.return_value = []
        mock_db.execute.return_value = result

    @pytest.mark.asyncio
    async def test_response_has_four_tabs(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        assert isinstance(result, DailyReportResponse)
        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.report_date == date(2026, 3, 15)
        assert result.available_rooms == 200

        tab_names = set(result.sections.keys())
        assert tab_names == {"Room Performance", "Ancillary Revenue", "Labor", "STR Competitive"}

    @pytest.mark.asyncio
    async def test_room_performance_sections(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        room_sections = result.sections["Room Performance"]
        assert len(room_sections) == 2
        assert room_sections[0].section_name == "Occupancy & Rate"
        assert room_sections[1].section_name == "Segmentation"

    @pytest.mark.asyncio
    async def test_occupancy_rate_row_count(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        occ_section = result.sections["Room Performance"][0]
        assert len(occ_section.rows) == 4  # rooms sold, occ%, ADR, RevPAR
        row_names = [r.line_name for r in occ_section.rows]
        assert "Rooms Sold" in row_names
        assert "Occupancy %" in row_names
        assert "ADR" in row_names
        assert "RevPAR" in row_names

    @pytest.mark.asyncio
    async def test_segmentation_has_total_row(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        seg_section = result.sections["Room Performance"][1]
        total_rows = [r for r in seg_section.rows if r.is_total]
        assert len(total_rows) == 1
        assert total_rows[0].line_name == "Total Room Revenue"

    @pytest.mark.asyncio
    async def test_ancillary_revenue_sections(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        anc_sections = result.sections["Ancillary Revenue"]
        assert len(anc_sections) == 2
        assert anc_sections[0].section_name == "F&B"
        assert anc_sections[1].section_name == "Other Revenue"

    @pytest.mark.asyncio
    async def test_fb_section_rows(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        fb_section = result.sections["Ancillary Revenue"][0]
        row_names = [r.line_name for r in fb_section.rows]
        assert "Restaurant" in row_names
        assert "Bar / Lounge" in row_names
        assert "Total F&B" in row_names
        assert "F&B per Occupied Room" in row_names

    @pytest.mark.asyncio
    async def test_labor_has_department_sections(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        labor_sections = result.sections["Labor"]
        section_names = [s.section_name for s in labor_sections]
        assert "Rooms" in section_names
        assert "F&B" in section_names
        assert "Spa" in section_names
        assert "Golf" in section_names
        assert "Mountain Ops" in section_names
        assert "A&G" in section_names
        assert "Maintenance" in section_names
        assert "Total Labor" in section_names

    @pytest.mark.asyncio
    async def test_labor_total_section_has_productivity_metrics(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        total_section = [s for s in result.sections["Labor"] if s.section_name == "Total Labor"][0]
        row_names = [r.line_name for r in total_section.rows]
        assert "Total Labor Wages" in row_names
        assert "FTEs" in row_names
        assert "MPOR" in row_names
        assert "Labor %" in row_names
        assert "Hrs / Occ Room" in row_names

    @pytest.mark.asyncio
    async def test_str_competitive_placeholder(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        str_sections = result.sections["STR Competitive"]
        assert len(str_sections) == 1
        row_names = [r.line_name for r in str_sections[0].rows]
        assert "Occupancy Index" in row_names
        assert "ADR Index" in row_names
        assert "RevPAR Index" in row_names

    @pytest.mark.asyncio
    async def test_dual_panel_values_with_data(self, service, mock_db):
        """Verify daily and MTD panels populate correctly from actuals."""
        data = {
            "rooms_sold": 150,
            "room_revenue": 3000000,  # $30,000 in cents
            "total_revenue": 5000000,
        }
        self._stub_db_rows(mock_db, data)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        occ_section = result.sections["Room Performance"][0]
        rooms_sold_row = next(r for r in occ_section.rows if r.line_name == "Rooms Sold")
        # All DB calls return the same stub, so daily_actual = 150
        assert rooms_sold_row.daily_actual == 150
        assert rooms_sold_row.unit == "integer"

    @pytest.mark.asyncio
    async def test_row_indent_and_flags(self, service, mock_db):
        self._stub_db_empty(mock_db)

        result = await service.get_daily_report(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            available_rooms=200,
            target_date=date(2026, 3, 15),
        )

        seg_section = result.sections["Room Performance"][1]
        transient = next(r for r in seg_section.rows if r.line_name == "Transient Rooms")
        assert transient.indent == 1
        assert transient.is_total is False
        assert transient.is_header is False

        total = next(r for r in seg_section.rows if r.line_name == "Total Room Revenue")
        assert total.is_total is True
        assert total.indent == 0


# ── API endpoint tests ────────────────────────────────────────────


class TestDailyReportAPI:

    def _make_mock_property(self):
        prop = MagicMock()
        prop.id = PROPERTY_ID
        prop.name = "Test Hotel"
        prop.code = "PROP1"
        prop.available_rooms = 200
        prop.is_active = True
        return prop

    @pytest.mark.asyncio
    async def test_get_daily_report_success(self, admin_client, mock_db):
        mock_report = DailyReportResponse(
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            report_date=date(2026, 3, 15),
            available_rooms=200,
            sections={
                "Room Performance": [],
                "Ancillary Revenue": [],
                "Labor": [],
                "STR Competitive": [],
            },
        )

        with patch("app.api.v1.daily_report.property_service") as mock_ps, \
             patch("app.api.v1.daily_report.daily_report_service") as mock_drs:
            mock_ps.get_property = AsyncMock(return_value=self._make_mock_property())
            mock_drs.get_daily_report = AsyncMock(return_value=mock_report)

            resp = await admin_client.get(
                f"/api/v1/daily-report/{PROPERTY_ID}?date=2026-03-15"
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["property_name"] == "Test Hotel"
        assert set(body["data"]["sections"].keys()) == {
            "Room Performance", "Ancillary Revenue", "Labor", "STR Competitive"
        }

    @pytest.mark.asyncio
    async def test_get_daily_report_property_not_found(self, admin_client, mock_db):
        with patch("app.api.v1.daily_report.property_service") as mock_ps:
            mock_ps.get_property = AsyncMock(return_value=None)

            resp = await admin_client.get(
                f"/api/v1/daily-report/{PROPERTY_ID}?date=2026-03-15"
            )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_daily_report_no_available_rooms(self, admin_client, mock_db):
        prop = self._make_mock_property()
        prop.available_rooms = None

        with patch("app.api.v1.daily_report.property_service") as mock_ps:
            mock_ps.get_property = AsyncMock(return_value=prop)

            resp = await admin_client.get(
                f"/api/v1/daily-report/{PROPERTY_ID}?date=2026-03-15"
            )

        assert resp.status_code == 422
