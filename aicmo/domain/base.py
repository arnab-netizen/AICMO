"""Base Pydantic model for all AICMO domain types."""

from pydantic import BaseModel, ConfigDict


class AicmoBaseModel(BaseModel):
    """Base Pydantic model for all AICMO domain types."""

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 style
