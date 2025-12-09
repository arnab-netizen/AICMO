"""Gateway adapters package."""

from .noop import NoOpEmailSender, NoOpSocialPoster, NoOpCRMSyncer

__all__ = [
    "NoOpEmailSender",
    "NoOpSocialPoster",
    "NoOpCRMSyncer",
]
