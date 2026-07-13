import pytest

from core.helper_protocol import validate_request
from core.validation import is_valid_ipv4, normalize_ipv4


def test_ipv4_validation_is_canonical_and_bounded():
    assert normalize_ipv4(" 1.1.1.1 ") == "1.1.1.1"
    assert is_valid_ipv4("255.255.255.255")
    for invalid in ("", "999.1.1.1", "1.2.3", "2001:4860:4860::8888", "01.1.1.1"):
        assert not is_valid_ipv4(invalid)


def test_helper_protocol_is_allow_listed():
    request = validate_request({
        "operation": "set",
        "primary": "8.8.8.8",
        "secondary": "8.8.4.4",
        "flush_after": True,
    })
    assert request.primary == "8.8.8.8"
    assert request.flush_after is True

    with pytest.raises(ValueError):
        validate_request({"operation": "powershell", "primary": "8.8.8.8"})
    with pytest.raises(ValueError):
        validate_request({"operation": "flush", "command": "whoami"})
    with pytest.raises(ValueError):
        validate_request({"operation": "set", "primary": "999.1.1.1"})
