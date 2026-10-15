import json
import os
import tempfile
from datetime import datetime

from paths import app_dir

STATE_FILE = "studio_modder_state.json"
MAX_HISTORY_ITEMS = 500


def _state_path():
    """Pasta gravável do estado.

    Prefere a pasta do app; se não puder gravar (ex.: instalado em
    C:\\Program Files), cai para %LOCALAPPDATA%\\StudioModderSuite para nunca
    quebrar o app com erro de caminho/permissão.
    """
    base = app_dir()
    try:
        probe = os.path.join(base, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("")
        os.remove(probe)
        return os.path.join(base, STATE_FILE)
    except OSError:
        fallback = os.path.join(tempfile.gettempdir(), "StudioModderSuite")
        try:
            os.makedirs(fallback, exist_ok=True)
        except OSError:
            fallback = tempfile.gettempdir()
        return os.path.join(fallback, STATE_FILE)


def _default_state():
    return {
        "presets": {},
        "history": []
    }


def load_state():
    path = _state_path()
    if not os.path.exists(path):
        return _default_state()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_state()
        data.setdefault("presets", {})
        data.setdefault("history", [])
        return data
    except Exception:
        return _default_state()


def save_state(state):
    path = _state_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError:
        # Estado é acessório: nunca derruba a ferramenta se não gravar.
        pass


def get_presets(tool_key):
    state = load_state()
    return state.get("presets", {}).get(tool_key, {})


def set_preset(tool_key, preset_name, payload):
    state = load_state()
    presets = state.setdefault("presets", {})
    tool_presets = presets.setdefault(tool_key, {})
    tool_presets[preset_name] = payload
    save_state(state)


def delete_preset(tool_key, preset_name):
    state = load_state()
    tool_presets = state.setdefault("presets", {}).setdefault(tool_key, {})
    if preset_name in tool_presets:
        del tool_presets[preset_name]
        save_state(state)


def append_history(tool_name, action, details):
    state = load_state()
    history = state.setdefault("history", [])
    history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool_name,
        "action": action,
        "details": details,
    })
    if len(history) > MAX_HISTORY_ITEMS:
        state["history"] = history[-MAX_HISTORY_ITEMS:]
    save_state(state)


def get_history(limit=None):
    state = load_state()
    history = list(state.get("history", []))
    if limit is not None and limit > 0:
        return history[-limit:]
    return history


def clear_history():
    state = load_state()
    state["history"] = []
    save_state(state)
