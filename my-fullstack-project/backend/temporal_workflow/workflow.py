from temporalio import workflow

@workflow.defn
class SiteGenerationWorkflow:
    @workflow.run
    async def run(self, site_data):
        # Call activities to generate the site
        result = await workflow.execute_activity(
            "generate_site_activity", site_data, start_to_close_timeout=timedelta(minutes=5)
        )
        return result

@workflow.defn
class AnotherWorkflow:
    @workflow.run
    async def run(self, input_data):
        # Implement another workflow logic here
        pass