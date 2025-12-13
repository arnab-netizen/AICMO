"""Billing - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import InvoiceId, PaymentId, ClientId

class InvoiceIssued(DomainEvent):
    invoice_id: InvoiceId
    client_id: ClientId
    total: float

class PaymentReceived(DomainEvent):
    payment_id: PaymentId
    invoice_id: InvoiceId
    amount: float

class PaymentFailed(DomainEvent):
    payment_id: PaymentId
    invoice_id: InvoiceId
    reason: str

__all__ = ["InvoiceIssued", "PaymentReceived", "PaymentFailed"]
