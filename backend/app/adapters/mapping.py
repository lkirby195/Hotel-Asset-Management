import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MappingEngine:
    """Translates external account codes to internal line_item codes."""

    def __init__(self, mapping: dict[str, str]):
        self._mapping = mapping
        self._warned: set[str] = set()

    @classmethod
    def from_file(cls, config_path: str, source: str = "profitsword") -> "MappingEngine":
        with open(config_path) as f:
            config = json.load(f)
        return cls(config.get(source, {}))

    @classmethod
    def default(cls) -> "MappingEngine":
        config_path = Path(__file__).parent / "mapping_config.json"
        if config_path.exists():
            return cls.from_file(str(config_path))
        return cls({})

    def translate(self, external_code: str) -> str | None:
        """Translate an external account code to an internal line_item code.

        Returns None if unmapped (logged as warning once per code).
        """
        internal = self._mapping.get(external_code)
        if internal is None and external_code not in self._warned:
            logger.warning(f"Unmapped account code: {external_code}")
            self._warned.add(external_code)
        return internal
