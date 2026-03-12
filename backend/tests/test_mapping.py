"""Tests for the MappingEngine."""

import json
import tempfile
from pathlib import Path

from app.adapters.mapping import MappingEngine


class TestMappingEngine:
    def test_translate_known_code(self):
        engine = MappingEngine({"RF0141": "room_revenue", "TOTGOP": "gross_operating_profit"})
        assert engine.translate("RF0141") == "room_revenue"
        assert engine.translate("TOTGOP") == "gross_operating_profit"

    def test_translate_unknown_returns_none(self):
        engine = MappingEngine({"RF0141": "room_revenue"})
        assert engine.translate("UNKNOWN_TAG") is None

    def test_translate_empty_mapping(self):
        engine = MappingEngine({})
        assert engine.translate("RF0141") is None

    def test_translate_empty_code(self):
        engine = MappingEngine({"": "empty_code"})
        assert engine.translate("") == "empty_code"

    def test_unmapped_warning_logged_once(self, caplog):
        engine = MappingEngine({"RF0141": "room_revenue"})
        # First call should warn
        engine.translate("UNMAPPED1")
        engine.translate("UNMAPPED1")
        engine.translate("UNMAPPED1")
        warnings = [r for r in caplog.records if "Unmapped account code: UNMAPPED1" in r.message]
        assert len(warnings) == 1

    def test_different_unmapped_codes_each_warned(self, caplog):
        engine = MappingEngine({})
        engine.translate("CODE_A")
        engine.translate("CODE_B")
        messages = [r.message for r in caplog.records]
        assert any("CODE_A" in m for m in messages)
        assert any("CODE_B" in m for m in messages)

    def test_from_file(self, tmp_path):
        config = {"profitsword": {"RF0001": "occupied_rooms", "RF0003": "adr"}}
        config_file = tmp_path / "mapping.json"
        config_file.write_text(json.dumps(config))

        engine = MappingEngine.from_file(str(config_file), source="profitsword")
        assert engine.translate("RF0001") == "occupied_rooms"
        assert engine.translate("RF0003") == "adr"
        assert engine.translate("MISSING") is None

    def test_from_file_missing_source(self, tmp_path):
        config = {"other_source": {"X": "y"}}
        config_file = tmp_path / "mapping.json"
        config_file.write_text(json.dumps(config))

        engine = MappingEngine.from_file(str(config_file), source="profitsword")
        assert engine.translate("X") is None

    def test_default_loads_mapping_config(self):
        engine = MappingEngine.default()
        # Should load the real mapping_config.json
        assert engine.translate("RF0141") == "room_revenue"
        assert engine.translate("TOTGOP") == "gross_operating_profit"
        assert engine.translate("EBITDA") == "ebitda"

    def test_default_with_nonexistent_file(self, monkeypatch):
        # Patch Path to make .exists() return False
        import app.adapters.mapping as mapping_mod
        original_from_file = MappingEngine.from_file

        def mock_exists(self):
            return False

        monkeypatch.setattr(Path, "exists", mock_exists)
        engine = MappingEngine.default()
        # Should return empty mapping
        assert engine.translate("RF0141") is None
