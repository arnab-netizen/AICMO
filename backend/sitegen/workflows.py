from __future__ import annotations
from dataclasses import dataclass
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from backend.sitegen.activities import ensure_home_page, record_deployment

TASK_QUEUE = "sitegen"


@dataclass
class SiteGenInput:
    site_id: int


@workflow.defn
class SiteGenWorkflow:
    @workflow.run
    async def run(self, inp: SiteGenInput) -> dict:
        try:
            page = await workflow.execute_activity(
                ensure_home_page,
                inp.site_id,
                schedule_to_close_timeout=workflow.timedelta(seconds=30),
            )
            dep_id = await workflow.execute_activity(
                record_deployment,
                inp.site_id,
                "succeeded",
                "Generated home page",
                schedule_to_close_timeout=workflow.timedelta(seconds=30),
            )
            return {"deployment_id": dep_id, "page": page}
        except Exception as e:
            # best-effort failure record
            try:
                await workflow.execute_activity(
                    record_deployment,
                    inp.site_id,
                    "failed",
                    str(e),
                    schedule_to_close_timeout=workflow.timedelta(seconds=30),
                )
            except Exception:
                pass
            raise
