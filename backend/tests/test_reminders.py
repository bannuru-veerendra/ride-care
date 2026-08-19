from datetime import date
from uuid import uuid4

from app.models.service_log import ServiceLog
from app.utils.reminders import find_active_next_service


def _log(
    *,
    visit_date: date,
    odometer: int,
    next_date: date | None = None,
    next_odo: int | None = None,
) -> ServiceLog:
    return ServiceLog(
        id=uuid4(),
        vehicle_id=uuid4(),
        date=visit_date,
        odometer=odometer,
        service_center="Test",
        total_cost=1000,
        services_done=["Oil"],
        next_service_date=next_date,
        next_service_odometer=next_odo,
    )


def test_fulfilled_date_schedule_returns_none():
    """A visit on the due date clears the older schedule."""
    due = date(2026, 3, 1)
    logs = [
        _log(visit_date=due, odometer=12000),
        _log(visit_date=date(2026, 1, 1), odometer=11000, next_date=due),
    ]
    assert find_active_next_service(logs) is None


def test_unfulfilled_past_due_schedule_still_active():
    """No later visit means the schedule stays active."""
    due = date(2026, 3, 1)
    logs = [
        _log(visit_date=date(2026, 1, 1), odometer=11000, next_date=due),
    ]
    assert find_active_next_service(logs) is not None


def test_intermediate_visit_does_not_clear_future_schedule():
    """A visit before the due date does not fulfill the schedule."""
    due = date(2026, 6, 1)
    logs = [
        _log(visit_date=date(2026, 3, 1), odometer=11500),
        _log(visit_date=date(2026, 1, 1), odometer=11000, next_date=due),
    ]
    active = find_active_next_service(logs)
    assert active is not None
    assert active.next_service_date == due


def test_both_date_and_km_must_be_met_when_both_set():
    """Date met but km short — schedule stays active."""
    due = date(2026, 3, 1)
    logs = [
        _log(visit_date=due, odometer=14000),
        _log(
            visit_date=date(2026, 1, 1),
            odometer=11000,
            next_date=due,
            next_odo=15000,
        ),
    ]
    active = find_active_next_service(logs)
    assert active is not None
    assert active.next_service_odometer == 15000
