from __future__ import annotations
from typing import Any, Dict
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from workers.sitegen import activities as A  # noqa


@workflow.defn
class SiteGenWorkflow:
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        site_id: str = params["site_id"]
        spec: Dict[str, Any] = params["spec"]
        provider: str = params.get("provider", "vercel")
        creds: Dict[str, Any] = params.get("creds", {})

        await workflow.execute_activity(
            A.sitearchitect_generate,
            site_id,
            start_to_close_timeout=workflow.timedelta(seconds=30),
        )

        copy = await workflow.execute_activity(
            A.copyweb_write_all,
            site_id,
            spec,
            start_to_close_timeout=workflow.timedelta(seconds=120),
            task_queue="sitegen.activities",
        )

        imgs = await workflow.execute_activity(
            A.visualgen_generate,
            site_id,
            spec,
            start_to_close_timeout=workflow.timedelta(seconds=120),
            task_queue="sitegen.activities",
        )

        repo_dir = await workflow.execute_activity(
            A.webbuilder_materialize,
            site_id,
            copy,
            imgs,
            start_to_close_timeout=workflow.timedelta(seconds=120),
            task_queue="sitegen.activities",
        )

        qa = await workflow.execute_activity(
            A.qaweb_run_checks,
            repo_dir,
            start_to_close_timeout=workflow.timedelta(seconds=180),
            task_queue="sitegen.activities",
        )

        preview_url = await workflow.execute_activity(
            A.deploy_preview,
            repo_dir,
            provider,
            creds,
            start_to_close_timeout=workflow.timedelta(seconds=120),
            task_queue="sitegen.activities",
        )

        prod_url = await workflow.execute_activity(
            A.deploy_promote,
            preview_url,
            provider,
            creds,
            start_to_close_timeout=workflow.timedelta(seconds=120),
            task_queue="sitegen.activities",
        )

        report = await workflow.execute_activity(
            A.reporting_lh_seo_report,
            prod_url,
            start_to_close_timeout=workflow.timedelta(seconds=180),
            task_queue="sitegen.activities",
        )

        return {
            "site_id": site_id,
            "repo_dir": repo_dir,
            "preview_url": preview_url,
            "prod_url": prod_url,
            "qa": qa,
            "report": report,
        }
