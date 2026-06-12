import re

import httpx
import pytest

from conftest import FakeWhoop, StaticTokens
from whoop_mcp.client import WhoopClient
from whoop_mcp.timeutil import parse_iso

pytestmark = pytest.mark.anyio


# Current public WHOOP GET surface that can return user data through this server.
# Trusted-partner endpoints and DELETE /v2/user/access are intentionally excluded.
EXPECTED_PUBLIC_GET_ENDPOINTS = {
    "GET /v1/activity-mapping/{activityV1Id}",
    "GET /v2/user/profile/basic",
    "GET /v2/user/measurement/body",
    "GET /v2/cycle",
    "GET /v2/cycle/{cycleId}",
    "GET /v2/cycle/{cycleId}/recovery",
    "GET /v2/cycle/{cycleId}/sleep",
    "GET /v2/recovery",
    "GET /v2/activity/sleep",
    "GET /v2/activity/sleep/{sleepId}",
    "GET /v2/activity/sleep/{sleepId}/stream",
    "GET /v2/activity/workout",
    "GET /v2/activity/workout/{workoutId}",
}


def _normalise_request(line: str) -> str:
    method, target = line.split(" ", 1)
    path = target.split("?", 1)[0].removeprefix("/developer")
    path = re.sub(
        r"^/v1/activity-mapping/\d+$",
        "/v1/activity-mapping/{activityV1Id}",
        path,
    )
    path = re.sub(r"^/v2/cycle/\d+/recovery$", "/v2/cycle/{cycleId}/recovery", path)
    path = re.sub(r"^/v2/cycle/\d+/sleep$", "/v2/cycle/{cycleId}/sleep", path)
    path = re.sub(r"^/v2/cycle/\d+$", "/v2/cycle/{cycleId}", path)
    path = re.sub(
        r"^/v2/activity/sleep/[^/]+/stream$",
        "/v2/activity/sleep/{sleepId}/stream",
        path,
    )
    path = re.sub(r"^/v2/activity/sleep/[^/]+$", "/v2/activity/sleep/{sleepId}", path)
    path = re.sub(r"^/v2/activity/workout/[^/]+$", "/v2/activity/workout/{workoutId}", path)
    return f"{method} {path}"


async def test_client_covers_current_public_whoop_get_data_surface(fake_whoop: FakeWhoop):
    fake_whoop.seed_days(4)
    sleep = fake_whoop.sleeps[-1]
    workout = fake_whoop.workouts[-1]
    cycle = fake_whoop.cycles[-1]
    fake_whoop.seed_stream(sleep["id"], parse_iso(sleep["start"]), parse_iso(sleep["end"]))

    client = WhoopClient(
        StaticTokens(),
        transport=httpx.MockTransport(fake_whoop.handler),
        cache_ttl=0,
    )
    try:
        await client.activity_mapping(sleep["v1_id"])
        await client.profile()
        await client.body_measurement()
        await client.cycles(max_records=1)
        await client.cycle(cycle["id"])
        await client.cycle_recovery(cycle["id"])
        await client.cycle_sleep(cycle["id"])
        await client.recoveries(max_records=1)
        await client.sleeps(max_records=1)
        await client.sleep(sleep["id"])
        await client.sleep_stream(sleep["id"])
        await client.workouts(max_records=1)
        await client.workout(workout["id"])
    finally:
        await client.aclose()

    observed = {_normalise_request(line) for line in fake_whoop.requests}
    assert EXPECTED_PUBLIC_GET_ENDPOINTS <= observed
