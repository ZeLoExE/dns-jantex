from core.powershell import quote_ps_literal


def test_powershell_literal_escapes_single_quotes():
    value = "Ethernet'; Write-Output pwned; #"
    assert quote_ps_literal(value) == "'Ethernet''; Write-Output pwned; #'"


def test_powershell_literal_rejects_non_string():
    try:
        quote_ps_literal(123)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("non-string PowerShell input was accepted")
