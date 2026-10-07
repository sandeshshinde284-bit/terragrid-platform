import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MockDataLoader:
    """
    Core service to load mock data and fallbacks from JSON files.
    Satisfies Copilot architectural requirements for strict data separation.
    """
    
    BASE_DIR = Path(__file__).parent.parent / "data"

    @classmethod
    def _load_json(cls, sub_dir: str, filename: str, inject_mock_flag: bool = False, inject_fallback_flag: bool = False) -> Any:
        file_path = cls.BASE_DIR / sub_dir / filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # If it's a list, we might want to inject flags into each item, 
                # but for simplicity, we assume the JSON files already have the flags or we inject if it's a dict.
                if isinstance(data, dict):
                    if inject_mock_flag:
                        data["is_mock_demo"] = True
                        data["ai_available"] = True
                        data["is_fallback"] = False
                    if inject_fallback_flag:
                        data["is_fallback"] = True
                        data["ai_available"] = False
                        data["is_mock_demo"] = False
                        
                return data
        except Exception as e:
            logger.error(f"MockDataLoader: Failed to load {filename} from {sub_dir}: {str(e)}")
            return [] if sub_dir == "mocks" and not filename.startswith("demo_") else {}

    @classmethod
    def load_fallback_ai_plan(cls) -> Dict[str, Any]:
        return cls._load_json("fallbacks", "ai_offline_plan.json", inject_fallback_flag=True)

    @classmethod
    def load_fallback_dossier(cls) -> Dict[str, Any]:
        return cls._load_json("fallbacks", "ai_offline_dossier.json", inject_fallback_flag=True)

    @classmethod
    def load_default_impact(cls) -> Dict[str, Any]:
        return cls._load_json("fallbacks", "default_impact.json", inject_fallback_flag=True)

    @classmethod
    def load_mock_plan(cls) -> Dict[str, Any]:
        return cls._load_json("mocks", "demo_plan.json", inject_mock_flag=True)

    @classmethod
    def load_mock_dossier(cls) -> Dict[str, Any]:
        return cls._load_json("mocks", "demo_dossier.json", inject_mock_flag=True)

    @classmethod
    def load_mock_incidents(cls, source: str) -> List[Dict[str, Any]]:
        filename = f"{source.lower()}.json"
        return cls._load_json("mocks", filename)
