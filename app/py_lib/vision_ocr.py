import base64
import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

try:
    from app import import_helper as ih
except Exception:
    ih = None

logger = logging.getLogger(__name__)


def extract_text(image, lang: str = "eng") -> Tuple[str, Optional[float], Optional[str]]:
    config = _load_config()
    if not config.get("endpoint"):
        return "", None, "VISION_OCR endpoint not configured"

    try:
        import cv2
    except Exception as exc:
        return "", None, f"OpenCV unavailable: {exc}"

    try:
        import requests
    except Exception as exc:
        return "", None, f"requests unavailable: {exc}"

    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        return "", None, "Failed to encode image"

    image_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
    payload = {
        "image_base64": image_b64,
        "lang": lang
    }
    if config.get("model"):
        payload["model"] = config["model"]
    payload.update(config.get("extra", {}))

    headers = {"Content-Type": "application/json"}
    if config.get("api_key"):
        headers["Authorization"] = f"Bearer {config['api_key']}"

    try:
        response = requests.post(
            config["endpoint"],
            json=payload,
            headers=headers,
            timeout=config.get("timeout", 30)
        )
        response.raise_for_status()
    except Exception as exc:
        return "", None, str(exc)

    try:
        data = response.json()
    except Exception:
        return "", None, "Non-JSON response from OCR service"

    text, confidence = _extract_text_from_response(
        data, config.get("text_path"), config.get("confidence_path"))
    if text is None:
        return "", None, "OCR response missing text"
    return text, confidence, None


def _load_config() -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    if ih is not None:
        try:
            config_value = ih.get_env_val("VISION_OCR")
            if isinstance(config_value, dict):
                config.update(config_value)
        except Exception:
            pass

    config.setdefault("endpoint", os.environ.get("VISION_OCR_ENDPOINT"))
    config.setdefault("api_key", os.environ.get("VISION_OCR_API_KEY"))
    config.setdefault("model", os.environ.get("VISION_OCR_MODEL"))
    config.setdefault("timeout", int(os.environ.get("VISION_OCR_TIMEOUT", "30")))

    if "text_path" not in config:
        config["text_path"] = os.environ.get("VISION_OCR_TEXT_PATH")
    if "confidence_path" not in config:
        config["confidence_path"] = os.environ.get("VISION_OCR_CONF_PATH")

    extra_raw = os.environ.get("VISION_OCR_EXTRA")
    if extra_raw and "extra" not in config:
        try:
            config["extra"] = json.loads(extra_raw)
        except Exception:
            config["extra"] = {}
    config.setdefault("extra", {})

    return config


def _extract_text_from_response(
    data: Any,
    text_path: Optional[str],
    confidence_path: Optional[str]
) -> Tuple[Optional[str], Optional[float]]:
    if text_path:
        text = _get_by_path(data, text_path)
    else:
        text = data.get("text") if isinstance(data, dict) else None

    confidence = None
    if confidence_path:
        confidence_val = _get_by_path(data, confidence_path)
        confidence = _to_float(confidence_val)
    elif isinstance(data, dict) and "confidence" in data:
        confidence = _to_float(data.get("confidence"))

    if isinstance(text, str):
        return text.strip(), confidence
    return None, confidence


def _get_by_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
