import datetime as dt

from hybrid_mailsec.features import build_window_samples
from hybrid_mailsec.parsers import ParsedEvent


def test_build_window_samples_labels_spam() -> None:
    events = [
        ParsedEvent(
            timestamp=dt.datetime(2026, 2, 13, 10, 5, 0),
            host_id="host1",
            service="smtp",
            account="example.com",
            sender="",
            src_ip="1.2.3.4",
            event_type="SMTP-IN:AUTH:AUTH+LOGIN",
            success=False,
            bytes_in=10,
            bytes_out=20,
            latency_ms=0,
            message_id="",
            spam_hint="",
        ),
        ParsedEvent(
            timestamp=dt.datetime(2026, 2, 13, 10, 6, 0),
            host_id="host1",
            service="mtafilter",
            account="example.com",
            sender="[SMTP:test@example.com]",
            src_ip="5.6.7.8",
            event_type="FILTER:spam:DELETE",
            success=False,
            bytes_in=0,
            bytes_out=0,
            latency_ms=0,
            message_id="abc.MAI",
            spam_hint="spam_delete",
        ),
    ]

    samples = build_window_samples(events=events, salt="x", window_minutes=15)
    assert len(samples) == 1
    assert samples[0].label == "spam"
