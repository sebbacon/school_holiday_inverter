import json
from icalendar import Calendar
from pathlib import Path
import pytest


@pytest.fixture
def sample_ics_path():
    return Path(__file__).parent / "sample.ics"


def test_holiday_generation(tmp_path, sample_ics_path, mocker):
    # Mock requests.get to return our test ICS data
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.text = sample_ics_path.read_text()

    # Import main after mocking so it uses the mocked requests
    from term_to_holiday import main

    main()

    # Verify JSON output
    with open("holidays.json") as f:
        holidays = json.load(f)

    expected_holidays = [
        {"name": "Christmas Holiday", "start": "2010-12-18", "end": "2011-01-03"},
        {"name": "Feb Half Term", "start": "2011-02-19", "end": "2011-02-27"},
    ]

    assert len(holidays) == len(expected_holidays)
    for expected, actual in zip(expected_holidays, holidays):
        assert actual["name"] == expected["name"]
        assert actual["start"] == expected["start"]
        assert actual["end"] == expected["end"]

    # Verify ICS output
    with open("holidays.ics", "rb") as f:
        cal = Calendar.from_ical(f.read())

    events = []
    for component in cal.walk("VEVENT"):
        events.append(
            {
                "name": str(component.get("SUMMARY")),
                "start": component.get("DTSTART").dt.isoformat(),
                "end": component.get("DTEND").dt.isoformat(),
            }
        )

    expected_ics_events = [
        {
            "name": "Christmas Holiday",
            "start": "2010-12-18",
            "end": "2011-01-04",  # ICS end date is exclusive
        },
        {"name": "Feb Half Term", "start": "2011-02-19", "end": "2011-02-28"},
    ]

    assert len(events) == len(expected_ics_events)
    for expected, actual in zip(expected_ics_events, events):
        assert actual["name"] == expected["name"]
        assert actual["start"] == expected["start"]
        assert actual["end"] == expected["end"]
