from fapilot.realtime import sse_event


def test_sse_event_formats_json_payload() -> None:
    event = sse_event({"ok": True}, event="ping", event_id="1")

    assert event == 'id: 1\nevent: ping\ndata: {"ok": true}\n\n'

