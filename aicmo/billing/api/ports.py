"""Billing - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.billing.api.dtos import InvoiceDTO, PaymentDTO, BillingStatusDTO
from aicmo.shared.ids import ClientId, InvoiceId, PaymentId

class InvoiceCreatePort(ABC):
    @abstractmethod
    def create_invoice(self, client_id: ClientId, line_items: list) -> InvoiceDTO:
        pass

class PaymentRecordPort(ABC):
    @abstractmethod
    def record_payment(self, invoice_id: InvoiceId, payment: PaymentDTO) -> None:
        pass

class BillingQueryPort(ABC):
    @abstractmethod
    def get_invoice(self, invoice_id: InvoiceId) -> InvoiceDTO:
        pass
    
    @abstractmethod
    def get_billing_status(self, client_id: ClientId) -> BillingStatusDTO:
        pass

__all__ = ["InvoiceCreatePort", "PaymentRecordPort", "BillingQueryPort"]
