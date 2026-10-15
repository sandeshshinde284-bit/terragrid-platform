"""
Raw data logger - writes the actual payload fetched from an external API or
returned by a Gemini call to logs/data/<source>/[<label>/]<timestamp>.json,
so it can be manually cross-checked against what the UI ends up showing.

This is separate from the existing [FEATURE_HEALTH] one-line summaries in
logs/backend/backend.log on purpose: those stay lightweight (one line per
event, safe to leave at INFO level permanently), while this writes the full
payload - potentially large - to its own file per call, organized folder-wise
by source so nothing has to be grepped out of a shared log. Nothing here
should ever be allowed to break the actual request, so every failure is
caught and logged as a warning rather than raised.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# backend/utils/data_logger.py -> backend/utils -> backend -> repo root
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_LOG_DIR = _ROOT_DIR / "logs" / "data"


def log_raw_data(
    source: str,
    data: Any,
    label: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Write one raw API/LLM payload to disk for manual cross-checking.

    Args:
        source: Top-level folder name, e.g. "nasa_eonet", "openweather_forecast",
            "gemini". One subfolder per source under logs/data/.
        data: The raw payload to write - a list/dict (events, parsed JSON) or
            a string (e.g. Gemini's raw response.text before JSON-cleaning).
        label: Optional second-level folder under `source`, e.g. a Gemini
            call's feature name ("deep_dossier", "agency_alerts") so a single
            "gemini" source still reads folder-wise per feature instead of
            one mixed pile of files.
        context: Optional small dict of extra identifying fields (location,
            city, event_type, ...) recorded alongside the payload.
    """
    try:
        target_dir = _DATA_LOG_DIR / source / label if label else _DATA_LOG_DIR / source
        target_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        filename = now.strftime("%Y%m%d_%H%M%S_%f")[:-3] + ".json"
        file_path = target_dir / filename

        envelope: Dict[str, Any] = {
            "logged_at_utc": now.isoformat(),
            "source": source,
        }
        if label:
            envelope["label"] = label
        if context:
            envelope["context"] = context
        envelope["data"] = data

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, default=str, ensure_ascii=False)

    except Exception as e:
        # Best-effort only - a cross-check log must never take down the
        # actual request it's trying to record.
        logger.warning(
            f"[FEATURE_HEALTH] feature=data_logger status=error source={source} "
            f"label={label} error={type(e).__name__}: {e}"
        )
