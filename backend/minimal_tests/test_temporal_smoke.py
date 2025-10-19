import os
import pytest
import asyncio

pytestmark = pytest.mark.e2e


def test_temporal_cluster_health():
    if not os.getenv("TEMPORAL_E2E"):
        pytest.skip("Set TEMPORAL_E2E=1 to run Temporal e2e smoke test.")

    address = os.getenv("TEMPORAL_ADDRESS", "127.0.0.1:7233")

    # Lazy import so normal unit runs don't need temporalio installed
    from temporalio.client import Client

    async def _check():
        from google.protobuf.empty_pb2 import Empty

        client = await Client.connect(address)
        info = await client.workflow_service.get_system_info(Empty())
        assert info.server_version, "Temporal server responded but version was empty"

    asyncio.run(_check())
