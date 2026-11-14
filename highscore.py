import json
import sys
from pathlib import Path

filepath = Path(__file__).parent / 'highscore.json'
storage_key = 'system-failure.best'


def load_high_score():
    try:
        if sys.platform == 'emscripten':
            import platform
            raw = platform.window.localStorage.getItem(storage_key)
            data = json.loads(str(raw)) if raw else {}
        else:
            data = json.loads(filepath.read_text())
        score = data.get('high_score', 0) if isinstance(data, dict) else data
        return score if type(score) is int and score >= 0 else 0
    except (ValueError, TypeError, OSError):
        return 0
    except Exception:
        if sys.platform == 'emscripten':
            return 0
        raise


def get_high_score(score):
    data = json.dumps({'high_score': score})
    if sys.platform == 'emscripten':
        import platform
        try:
            platform.window.localStorage.setItem(storage_key, data)
        except Exception:
            pass
    else:
        filepath.write_text(data)
