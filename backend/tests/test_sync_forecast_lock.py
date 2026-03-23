"""Tests for the lock_monthly_forecast Celery task."""

from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app.tasks.sync_forecast_lock import lock_monthly_forecast


class TestDefaultMonthCalculation:
    """Verify prior-month defaulting when year/month are None."""

    @patch("app.tasks.sync_forecast_lock._get_sync_engine")
    @patch("app.tasks.sync_forecast_lock._get_adapter")
    @patch("app.tasks.sync_forecast_lock.date")
    def test_default_month_calculation(self, mock_date, mock_adapter, mock_engine):
        mock_date.today.return_value = date(2026, 3, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        adapter = MagicMock()
        adapter.fetch_forecasts.return_value = []
        mock_adapter.return_value = adapter

        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        mock_engine.return_value.begin.return_value.__enter__ = MagicMock(return_value=session)
        mock_engine.return_value.begin.return_value.__exit__ = MagicMock(return_value=False)

        mock_session_cls = MagicMock()
        mock_session_ctx = MagicMock()
        mock_session_ctx.execute.return_value.fetchall.return_value = []
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session_ctx)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.tasks.sync_forecast_lock.Session", mock_session_cls):
            result = lock_monthly_forecast("tenant-1", year=None, month=None)

        assert result["year"] == 2026
        assert result["month"] == 2

    @patch("app.tasks.sync_forecast_lock._get_sync_engine")
    @patch("app.tasks.sync_forecast_lock._get_adapter")
    @patch("app.tasks.sync_forecast_lock.date")
    def test_january_wraps_to_december(self, mock_date, mock_adapter, mock_engine):
        mock_date.today.return_value = date(2026, 1, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        adapter = MagicMock()
        adapter.fetch_forecasts.return_value = []
        mock_adapter.return_value = adapter

        mock_session_cls = MagicMock()
        mock_session_ctx = MagicMock()
        mock_session_ctx.execute.return_value.fetchall.return_value = []
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session_ctx)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.tasks.sync_forecast_lock.Session", mock_session_cls):
            result = lock_monthly_forecast("tenant-1", year=None, month=None)

        assert result["year"] == 2025
        assert result["month"] == 12


class TestPartialNoneRaises:
    """Verify that passing only year or only month raises ValueError."""

    def test_year_only_raises(self):
        with pytest.raises(ValueError, match="both be provided or both be None"):
            lock_monthly_forecast("tenant-1", year=2026, month=None)

    def test_month_only_raises(self):
        with pytest.raises(ValueError, match="both be provided or both be None"):
            lock_monthly_forecast("tenant-1", year=None, month=3)
