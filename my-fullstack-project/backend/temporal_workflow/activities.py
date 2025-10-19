from temporalio import activity


@activity.defn
async def example_activity(param1: str, param2: int) -> str:
    # Simulate some processing
    result = f"Processed {param1} with number {param2}"
    return result


@activity.defn
async def another_activity(data: dict) -> dict:
    # Simulate processing of a dictionary
    data["processed"] = True
    return data
