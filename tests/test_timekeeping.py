from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pytest
from zoneinfo import ZoneInfo

from nova.system.timekeeping import (
    AgentCalendar,
    AgentClock,
    CalendarEvent,
    TimeProfile,
    Timekeeper,
    WorkingHours,
    build_default_timekeeper,
)


def _sample_event(start: datetime, minutes: int = 30) -> CalendarEvent:
    return CalendarEvent(
        title="sample",
        start=start,
        end=start + timedelta(minutes=minutes),
    )


def test_calendar_event_overlap_and_duration() -> None:
    tz = ZoneInfo("UTC")
    start = datetime(2024, 1, 1, 9, 0, tzinfo=tz)
    event_a = _sample_event(start)
    event_b = _sample_event(start + timedelta(minutes=15))
    event_c = _sample_event(start + timedelta(minutes=45))

    assert event_a.duration() == timedelta(minutes=30)
    assert event_a.overlaps(event_b) is True
    assert event_a.overlaps(event_c) is False


def test_agent_calendar_schedules_in_order_and_returns_conflicts() -> None:
    tz = ZoneInfo("UTC")
    calendar = AgentCalendar()

    first = _sample_event(datetime(2024, 1, 1, 9, 0, tzinfo=tz))
    second = _sample_event(datetime(2024, 1, 1, 10, 0, tzinfo=tz))
    overlapping = _sample_event(datetime(2024, 1, 1, 9, 15, tzinfo=tz))

    assert calendar.schedule_event(first) == []
    assert calendar.schedule_event(second) == []
    conflicts = calendar.schedule_event(overlapping)
    assert conflicts == [first]

    events = list(calendar.iter_events())
    assert events[0] is first
    assert events[1] is overlapping
    assert events[2] is second


def test_agent_clock_handles_drift_and_conversion() -> None:
    utc = ZoneInfo("UTC")
    berlin = ZoneInfo("Europe/Berlin")
    reference = datetime(2024, 1, 1, 12, 0, tzinfo=utc)

    clock = AgentClock(identifier="nova", timezone=berlin)
    assert clock.now(reference=reference) == reference.astimezone(berlin)

    clock.adjust(timedelta(minutes=5))
    expected = reference.astimezone(berlin) + timedelta(minutes=5)
    assert clock.now(reference=reference) == expected

    clock.reset()
    assert clock.now(reference=reference) == reference.astimezone(berlin)


def test_time_profile_working_hours_and_next_window() -> None:
    utc = ZoneInfo("UTC")
    clock = AgentClock(identifier="nova", timezone=utc)
    calendar = AgentCalendar()
    working_hours = {0: WorkingHours(start=time(9, 0), end=time(17, 0))}
    profile = TimeProfile(
        identifier="nova",
        display_name="Nova",
        clock=clock,
        calendar=calendar,
        working_hours=working_hours,
    )

    within = datetime(2024, 1, 1, 10, 0, tzinfo=utc)
    assert profile.is_within_working_hours(within) is True

    outside = datetime(2024, 1, 1, 20, 0, tzinfo=utc)
    assert profile.is_within_working_hours(outside) is False

    start, end = profile.next_focus_window(outside)
    assert start > outside
    assert end - start == timedelta(hours=8)


def test_timekeeper_registers_profiles_and_provides_upcoming_events() -> None:
    tz = ZoneInfo("UTC")
    keeper = Timekeeper()
    profile = keeper.register_profile(
        "nova",
        timezone=tz,
        working_hours={0: (time(9, 0), time(17, 0))},
    )

    event = _sample_event(datetime(2024, 1, 1, 9, 0, tzinfo=tz))
    conflicts = keeper.schedule_event("nova", event)
    assert conflicts == []

    upcoming = keeper.upcoming_events(
        "nova",
        reference=datetime(2024, 1, 1, 8, 0, tzinfo=tz),
    )
    assert upcoming == [event]
    assert keeper.get_profile("nova") is profile


def test_build_default_timekeeper_sets_up_three_profiles() -> None:
    keeper = build_default_timekeeper()
    identifiers = {profile.identifier for profile in keeper.list_profiles()}
    assert {"spark-sophia", "nova", "aura"}.issubset(identifiers)

    spark_profile = keeper.get_profile("spark-sophia")
    assert spark_profile is not None
    assert spark_profile.display_name == "Spark Sophia"
    assert any(
        "Check" in event.title for event in spark_profile.calendar.to_list()
    )

    nova_profile = keeper.get_profile("nova")
    assert nova_profile is not None
    berlin_tz = ZoneInfo("Europe/Berlin")
    utc = ZoneInfo("UTC")

    for event in spark_profile.calendar.to_list():
        assert event.start.tzinfo == berlin_tz

    for event in nova_profile.calendar.to_list():
        assert event.start.tzinfo == utc

    aura_profile = keeper.get_profile("aura")
    assert aura_profile is not None
    assert aura_profile.display_name.startswith("Aurora")


def test_calendar_event_requires_timezone_information() -> None:
    naive_start = datetime(2024, 1, 1, 9, 0)
    naive_end = datetime(2024, 1, 1, 10, 0)
    with pytest.raises(ValueError):
        CalendarEvent(title="invalid", start=naive_start, end=naive_end)

