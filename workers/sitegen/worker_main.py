from __future__ import annotations
import asyncio
import os
from temporalio.worker import Worker
from temporalio.client import Client
from workers.sitegen.workflows import SiteGenWorkflow
from workers.sitegen import activities as A


async def main() -> None:
    address = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
    task_queue = os.getenv("SITEGEN_TASK_QUEUE", "sitegen.activities")
    client = await Client.connect(address)
    worker = Worker(
        client=client,
        task_queue=task_queue,
        workflows=[SiteGenWorkflow],
        activities=[
            A.sitearchitect_generate,
            A.copyweb_write_all,
            A.visualgen_generate,
            A.webbuilder_materialize,
            A.qaweb_run_checks,
            A.deploy_preview,
            A.deploy_promote,
            A.reporting_lh_seo_report,
        ],
    )
    print(f"[SiteGen Worker] Connected to {address}, tq={task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
