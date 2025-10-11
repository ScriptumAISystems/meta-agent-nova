"""Timekeeping utilities for Nova and the Spark Sophia ecosystem.

The module models a lightweight time coordination layer that can be
used by Nova and its specialist agents.  It provides simple abstractions
for agent clocks (timezone awareness + drift handling) and collaborative
calendars that keep track of planned activities.  The default helper
``build_default_timekeeper`` wires these pieces together for Spark
Sophia, Nova and Aura/Aurora so that they share a consistent schedule.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Sequence
from zoneinfo import ZoneInfo

__all__ = [
    "CalendarEvent",
    "AgentCalendar",
    "AgentClock",
    "WorkingHours",
    "TimeProfile",
    "Timekeeper",
    "build_default_timekeeper",
]


@dataclass(slots=True)
class CalendarEvent:
    """Single entry in an agent calendar."""

    title: str
    start: datetime
    end: datetime
    location: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("CalendarEvent start/end must be timezone-aware datetimes.")
        if self.end <= self.start:
            raise ValueError("CalendarEvent end must be after start.")

    def duration(self) -> timedelta:
        """Return the event duration."""

        return self.end - self.start

    def overlaps(self, other: "CalendarEvent") -> bool:
        """Return ``True`` if the event overlaps with ``other``."""

        latest_start = max(self.start, other.start)
        earliest_end = min(self.end, other.end)
        return latest_start < earliest_end

    def to_dict(self) -> dict[str, object]:
        """Return a serialisable representation of the event."""

        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "description": self.description,
        }


class AgentCalendar:
    """Ordered collection of :class:`CalendarEvent` objects."""

    def __init__(self, events: Iterable[CalendarEvent] | None = None) -> None:
        self._events: List[CalendarEvent] = []
        if events:
            for event in sorted(events, key=lambda item: item.start):
                self._insert_event(event)

    def _insert_event(self, event: CalendarEvent) -> None:
        positions = [existing.start for existing in self._events]
        index = bisect_left(positions, event.start)
        self._events.insert(index, event)

    def schedule_event(self, event: CalendarEvent) -> List[CalendarEvent]:
        """Add ``event`` to the calendar and return conflicting events."""

        conflicts = [existing for existing in self._events if existing.overlaps(event)]
        self._insert_event(event)
        return conflicts

    def upcoming_events(
        self,
        *,
        reference: datetime | None = None,
        limit: int | None = None,
    ) -> List[CalendarEvent]:
        """Return future events ordered by start time."""

        if reference is None:
            reference = datetime.now(timezone.utc)
        selected = [event for event in self._events if event.end > reference]
        if limit is not None and limit >= 0:
            return selected[:limit]
        return selected

    def agenda_for_day(self, day: date | datetime) -> List[CalendarEvent]:
        """Return the events scheduled for the calendar date ``day``."""

        if isinstance(day, datetime):
            target = day.date()
        else:
            target = day
        return [event for event in self._events if event.start.date() == target]

    def iter_events(self) -> Iterator[CalendarEvent]:
        """Yield events in chronological order."""

        yield from self._events

    def to_list(self) -> List[CalendarEvent]:
        """Return a shallow copy of the scheduled events."""

        return list(self._events)


@dataclass(slots=True)
class AgentClock:
    """Maintains local time information for an agent."""

    identifier: str
    timezone: ZoneInfo
    drift: timedelta = field(default_factory=timedelta)

    def now(self, *, reference: datetime | None = None) -> datetime:
        """Return the current local time with drift applied."""

        base = reference or datetime.now(timezone.utc)
        localised = base.astimezone(self.timezone)
        return localised + self.drift

    def as_local(self, moment: datetime | None = None) -> datetime:
        """Convert ``moment`` to the local timezone and apply drift."""

        return self.now(reference=moment)

    def adjust(self, delta: timedelta) -> None:
        """Modify the internal drift by ``delta``."""

        self.drift += delta

    def reset(self) -> None:
        """Reset the drift to zero."""

        self.drift = timedelta(0)


@dataclass(slots=True)
class WorkingHours:
    """Represents a contiguous focus window within a day."""

    start: time
    end: time

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("WorkingHours end must be after start.")

    def contains(self, moment: time) -> bool:
        """Return ``True`` if ``moment`` falls within the interval."""

        candidate = moment.replace(tzinfo=None)
        return self.start <= candidate < self.end

    def to_tuple(self) -> tuple[str, str]:
        return (self.start.strftime("%H:%M"), self.end.strftime("%H:%M"))


@dataclass(slots=True)
class TimeProfile:
    """Encapsulates the clock and calendar for a single agent."""

    identifier: str
    display_name: str
    clock: AgentClock
    calendar: AgentCalendar
    working_hours: Dict[int, WorkingHours] = field(default_factory=dict)

    def is_within_working_hours(self, moment: datetime | None = None) -> bool:
        """Return ``True`` if ``moment`` is inside the defined focus window."""

        local = self.clock.as_local(moment)
        hours = self.working_hours.get(local.weekday())
        if hours is None:
            return False
        return hours.contains(local.timetz().replace(tzinfo=None))

    def next_focus_window(
        self, moment: datetime | None = None
    ) -> tuple[datetime, datetime] | None:
        """Return the next focus window starting at or after ``moment``."""

        local = self.clock.as_local(moment)
        for offset in range(0, 14):
            candidate = local + timedelta(days=offset)
            hours = self.working_hours.get(candidate.weekday())
            if hours is None:
                continue
            start_dt = datetime.combine(
                candidate.date(),
                hours.start,
                tzinfo=self.clock.timezone,
            ) + self.clock.drift
            end_dt = datetime.combine(
                candidate.date(),
                hours.end,
                tzinfo=self.clock.timezone,
            ) + self.clock.drift
            if offset == 0:
                current_time = local.timetz().replace(tzinfo=None)
                if current_time >= hours.end:
                    continue
                if current_time > hours.start:
                    start_dt = local
            return start_dt, end_dt
        return None

    def to_dict(self) -> dict[str, object]:
        """Serialise the profile for logging or introspection."""

        return {
            "identifier": self.identifier,
            "display_name": self.display_name,
            "timezone": getattr(self.clock.timezone, "key", str(self.clock.timezone)),
            "drift_seconds": int(self.clock.drift.total_seconds()),
            "working_hours": {
                str(weekday): window.to_tuple() for weekday, window in self.working_hours.items()
            },
            "events": [event.to_dict() for event in self.calendar.to_list()],
        }


class Timekeeper:
    """Registry managing time profiles for agents."""

    def __init__(self) -> None:
        self._profiles: MutableMapping[str, TimeProfile] = {}

    @staticmethod
    def _normalise_timezone(value: ZoneInfo | str) -> ZoneInfo:
        if isinstance(value, ZoneInfo):
            return value
        return ZoneInfo(str(value))

    @staticmethod
    def _normalise_hours(working_hours: Mapping[int, WorkingHours | Sequence[time | str]] | None) -> Dict[int, WorkingHours]:
        if not working_hours:
            return {}
        result: Dict[int, WorkingHours] = {}
        for weekday, hours in working_hours.items():
            if isinstance(hours, WorkingHours):
                window = hours
            else:
                if len(hours) != 2:
                    raise ValueError("Working hour entries must provide start and end times.")
                start_raw, end_raw = hours
                start = _ensure_time(start_raw)
                end = _ensure_time(end_raw)
                window = WorkingHours(start=start, end=end)
            result[int(weekday) % 7] = window
        return result

    def register_profile(
        self,
        identifier: str,
        *,
        display_name: str | None = None,
        timezone: ZoneInfo | str,
        working_hours: Mapping[int, WorkingHours | Sequence[time | str]] | None = None,
        events: Iterable[CalendarEvent] | None = None,
    ) -> TimeProfile:
        """Create and register a :class:`TimeProfile` for ``identifier``."""

        tz = self._normalise_timezone(timezone)
        clock = AgentClock(identifier=identifier, timezone=tz)
        calendar = AgentCalendar(events)
        hours = self._normalise_hours(working_hours)
        profile = TimeProfile(
            identifier=identifier,
            display_name=display_name or identifier.replace("-", " ").title(),
            clock=clock,
            calendar=calendar,
            working_hours=hours,
        )
        self._profiles[identifier] = profile
        return profile

    def get_profile(self, identifier: str) -> TimeProfile | None:
        return self._profiles.get(identifier)

    def require_profile(self, identifier: str) -> TimeProfile:
        profile = self.get_profile(identifier)
        if profile is None:
            raise KeyError(f"No time profile registered for '{identifier}'.")
        return profile

    def schedule_event(self, identifier: str, event: CalendarEvent) -> List[CalendarEvent]:
        profile = self.require_profile(identifier)
        return profile.calendar.schedule_event(event)

    def upcoming_events(
        self,
        identifier: str,
        *,
        reference: datetime | None = None,
        limit: int | None = None,
    ) -> List[CalendarEvent]:
        profile = self.require_profile(identifier)
        return profile.calendar.upcoming_events(reference=reference, limit=limit)

    def list_profiles(self) -> List[TimeProfile]:
        return list(self._profiles.values())

    def to_dict(self) -> dict[str, object]:
        return {identifier: profile.to_dict() for identifier, profile in self._profiles.items()}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ensure_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    if not isinstance(value, str):
        raise TypeError("Time values must be datetime.time or 'HH:MM' strings.")
    cleaned = value.strip()
    hour_part, minute_part = cleaned.split(":", 1)
    return time(int(hour_part), int(minute_part))


def _default_working_hours() -> Dict[int, WorkingHours]:
    start = time(9, 0)
    end = time(17, 30)
    return {weekday: WorkingHours(start=start, end=end) for weekday in range(0, 5)}


def _shared_sync_event(
    *,
    title: str,
    start_local: datetime,
    duration: timedelta,
    description: str,
) -> CalendarEvent:
    return CalendarEvent(
        title=title,
        start=start_local,
        end=start_local + duration,
        description=description,
    )


def build_default_timekeeper() -> Timekeeper:
    """Return a :class:`Timekeeper` configured for Spark Sophia, Nova and Aura."""

    timekeeper = Timekeeper()
    shared_hours = _default_working_hours()
    berlin = ZoneInfo("Europe/Berlin")
    utc = ZoneInfo("UTC")

    spark_profile = timekeeper.register_profile(
        "spark-sophia",
        display_name="Spark Sophia",
        timezone=berlin,
        working_hours=shared_hours,
    )
    nova_profile = timekeeper.register_profile(
        "nova",
        display_name="Nova Orchestrator",
        timezone=utc,
        working_hours=shared_hours,
    )
    aura_profile = timekeeper.register_profile(
        "aura",
        display_name="Aurora Observability",
        timezone=berlin,
        working_hours=shared_hours,
    )

    # Shared coordination rituals – scheduled relative to Berlin time.
    kickoff = datetime(2024, 6, 17, 9, 0, tzinfo=berlin)
    planning = datetime(2024, 6, 17, 14, 0, tzinfo=berlin)
    retro = datetime(2024, 6, 21, 16, 0, tzinfo=berlin)

    events = [
        (spark_profile, "Spark Sophia Morgen-Check-in", kickoff, timedelta(minutes=30)),
        (nova_profile, "Nova Strategieabgleich", kickoff.astimezone(utc), timedelta(minutes=30)),
        (aura_profile, "Aurora Observability Sync", kickoff, timedelta(minutes=30)),
        (spark_profile, "Hardware Planungsrunde", planning, timedelta(minutes=45)),
        (nova_profile, "Nova Wochenplanung", planning.astimezone(utc), timedelta(minutes=45)),
        (aura_profile, "Aurora Dashboard Planung", planning, timedelta(minutes=45)),
        (spark_profile, "Wöchentliche Retrospektive", retro, timedelta(minutes=40)),
        (nova_profile, "Nova Governance Review", retro.astimezone(utc), timedelta(minutes=40)),
        (aura_profile, "Aurora Reporting Review", retro, timedelta(minutes=40)),
    ]

    for profile, title, start, duration in events:
        event = _shared_sync_event(
            title=title,
            start_local=start,
            duration=duration,
            description="Gemeinsamer Termin zur Synchronisation zwischen Spark Sophia, Nova und Aurora.",
        )
        profile.calendar.schedule_event(event)

    return timekeeper
