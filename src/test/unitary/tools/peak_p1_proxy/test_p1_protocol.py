from tools.peak_p1_proxy.p1_protocol import (
    P1ProtocolError,
    format_artisan_read_response,
    parse_p1_group_response,
)


def test_parse_3400_response_maps_bt_and_et() -> None:
    values = parse_p1_group_response("3400", "171.51,159.82,171.51,C")

    assert values.at == 171.51
    assert values.bt == 159.82
    assert values.et == 171.51
    assert values.exhaust is None
    assert values.inlet is None


def test_parse_1200_response_maps_exhaust_and_inlet() -> None:
    values = parse_p1_group_response("1200", "171.51,176.10,166.09,C")

    assert values.at == 171.51
    assert values.exhaust == 176.10
    assert values.inlet == 166.09
    assert values.bt is None
    assert values.et is None


def test_format_artisan_read_response_uses_tc4_csv_shape() -> None:
    line = format_artisan_read_response(at=171.51, first=159.82, second=171.51)

    assert line == "171.51,159.82,171.51,C\r\n"


def test_parse_rejects_bad_unit_marker() -> None:
    try:
        parse_p1_group_response("3400", "171.51,159.82,171.51,K")
    except P1ProtocolError as exc:
        assert "invalid P1 response" in str(exc)
    else:
        raise AssertionError("expected P1ProtocolError")
