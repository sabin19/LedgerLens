from pydantic import BaseModel, Field
from typing import List, Optional

class LineItem(BaseModel):
    description: str = Field(
        description="The description of the line item or product."
    )
    quantity: Optional[float] = Field(
        None, 
        description="The quantity of the item purchased."
    )
    unit_price: Optional[float] = Field(
        None, 
        description="The price of a single unit."
    )
    amount: float = Field(
        description="The total cost for this specific line item."
    )
    confidence: float = Field(
        description="Confidence score for this line item extraction, represented as a float between 0.0 and 1.0."
    )

class InvoiceSchema(BaseModel):
    vendor: str = Field(
        description="The name of the vendor, merchant, or company issuing the receipt/invoice."
    )
    invoice_number: Optional[str] = Field(
        None, 
        description="The unique invoice, receipt, or transaction number."
    )
    date: str = Field(
        description="The date the invoice was issued, formatted as YYYY-MM-DD."
    )
    currency: str = Field(
        description="The 3-letter currency code (e.g., USD, INR, EUR)."
    )
    subtotal: Optional[float] = Field(
        None, 
        description="The subtotal amount before taxes or discounts."
    )
    tax: Optional[float] = Field(
        None, 
        description="The total tax amount applied to the invoice."
    )
    total: float = Field(
        description="The final total amount charged on the receipt or invoice."
    )
    line_items: List[LineItem] = Field(
        description="A list containing all the individual items purchased."
    )
    overall_confidence: float = Field(
        description="Confidence score for the overall document extraction, represented as a float between 0.0 and 1.0."
    )