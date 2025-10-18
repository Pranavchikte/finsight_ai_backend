from pydantic import BaseModel, Field, model_validator
from typing import Literal

PREDEFINED_CATEGORIES = {
    "Food & Dining", "Transportation", "Utilities", "Housing", "Shopping",
    "Entertainment", "Health & Wellness", "Groceries", "Bills & Fees",
    "Travel", "Education", "Other"
}

class AddTransactionSchema(BaseModel):
   
    mode: Literal['ai', 'manual'] 
    text: str | None = None
    amount: float | None = Field(None, gt=0) 
    category: str | None = None
    description: str | None = None

    # This replaces BOTH of the old validators.
    # It runs after all other fields are validated.
    @model_validator(mode='after')
    def check_fields_for_mode(self):
        # 'self' refers to the model instance with all the data
        if self.mode == 'ai' and not self.text:
            raise ValueError('The "text" field is required for AI mode.')
        
        if self.mode == 'manual':
            if not self.amount or not self.category or not self.description:
                raise ValueError('Amount, category, and description are required for manual mode.')
            if self.category not in PREDEFINED_CATEGORIES:
                raise ValueError(f'Invalid category. Must be one of {", ".join(PREDEFINED_CATEGORIES)}')
        
        return self # Always return the model instance