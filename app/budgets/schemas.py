from pydantic import BaseModel, Field, field_validator
from app.transactions.schemas import PREDEFINED_CATEGORIES
from typing import Literal
from datetime import datetime

class BudgetSchema(BaseModel):
    category: str = Field(...)
    # FIX #5: Budget Schema Validation (Added le=10000000)
    limit: float = Field(..., gt=0, le=10000000)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2024)

    @field_validator('category')
    def category_must_be_predefined(cls, v):
        if v not in PREDEFINED_CATEGORIES:
            raise ValueError(f"Category must be one of {PREDEFINED_CATEGORIES}")
        return v