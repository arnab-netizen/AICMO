from fastapi import APIRouter

router = APIRouter()


@router.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}


@router.post("/items/")
async def create_item(item: dict):
    return {"item": item}


@router.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    return {"item_id": item_id, "updated_item": item}


@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}
