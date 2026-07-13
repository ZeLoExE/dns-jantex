
from core.storage import atomic_write_json, load_json


def test_atomic_json_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    atomic_write_json(path, {"language": "fa", "favorites": ["Cloudflare"]})
    assert load_json(path, {}) == {"language": "fa", "favorites": ["Cloudflare"]}
    assert not list(tmp_path.glob("*.tmp"))


def test_corrupt_json_is_preserved(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text("{not-json", encoding="utf-8")
    assert load_json(path, []) == []
    assert not path.exists()
    corrupt = list(tmp_path.glob("profiles.json.corrupt-*"))
    assert len(corrupt) == 1
    assert corrupt[0].read_text(encoding="utf-8") == "{not-json"
