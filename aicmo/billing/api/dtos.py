"""Billing - DTOs."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from aicmo.shared.ids import ClientId, InvoiceId, PaymentId

class LineItemDTO(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class InvoiceDTO(BaseModel):
    invoice_id: InvoiceId
    client_id: ClientId
    line_items: List[LineItemDTO]
    subtotal: float
    tax: float
    total: float
    issued_at: datetime
    due_date: datetime
    status: str  # "draft", "sent", "paid", "overdue"

class PaymentDTO(BaseModel):
    payment_id: PaymentId
    invoice_id: InvoiceId
    amount: float
    method: str
    transaction_id: Optional[str] = None
    paid_at: datetime

class BillingStatusDTO(BaseModel):
    client_id: ClientId
    outstanding_balance: float
    overdue_count: int
    last_payment_at: Optional[datetime] = None

__all__ = ["LineItemDTO", "InvoiceDTO", "PaymentDTO", "BillingStatusDTO"]
