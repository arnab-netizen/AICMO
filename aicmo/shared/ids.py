"""
Shared ID type helpers for AICMO contracts.

Provides standardized ID types for use in DTOs and domain events.
All IDs are strings to allow flexibility (ULID, UUID, etc).
"""

from typing import NewType

# Business entity IDs
LeadId = NewType("LeadId", str)
CampaignId = NewType("CampaignId", str)
ClientId = NewType("ClientId", str)
ProjectId = NewType("ProjectId", str)
BriefId = NewType("BriefId", str)
StrategyId = NewType("StrategyId", str)
DraftId = NewType("DraftId", str)
AssetId = NewType("AssetId", str)
QcResultId = NewType("QcResultId", str)
ReviewPackageId = NewType("ReviewPackageId", str)
DeliveryPackageId = NewType("DeliveryPackageId", str)
ReportId = NewType("ReportId", str)
InvoiceId = NewType("InvoiceId", str)
PaymentId = NewType("PaymentId", str)

# Cross-cutting IDs
UserId = NewType("UserId", str)
WorkflowId = NewType("WorkflowId", str)
SagaId = NewType("SagaId", str)
EventId = NewType("EventId", str)
CorrelationId = NewType("CorrelationId", str)
TraceId = NewType("TraceId", str)
SpanId = NewType("SpanId", str)

__all__ = [
    # Business
    "LeadId",
    "CampaignId",
    "ClientId",
    "ProjectId",
    "BriefId",
    "StrategyId",
    "DraftId",
    "AssetId",
    "QcResultId",
    "ReviewPackageId",
    "DeliveryPackageId",
    "ReportId",
    "InvoiceId",
    "PaymentId",
    # Cross-cutting
    "UserId",
    "WorkflowId",
    "SagaId",
    "EventId",
    "CorrelationId",
    "TraceId",
    "SpanId",
]
