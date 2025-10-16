from __future__ import annotations
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from backend.sitegen.workflows import SiteGenWorkflow, TASK_QUEUE
from backend.sitegen.activities import ensure_home_page, record_deployment

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

async def main() -> None:
    client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SiteGenWorkflow],
        activities=[ensure_home_page, record_deployment],
    )
    print(f"⚙️  SiteGen worker started (namespace={TEMPORAL_NAMESPACE}, task_queue={TASK_QUEUE})")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
