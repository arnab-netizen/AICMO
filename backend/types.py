from typing import TypedDict, NotRequired, Protocol, runtime_checkable


class TasteConfig(TypedDict):
    model: str
    temperature: float
    top_p: NotRequired[float]
    max_tokens: NotRequired[int]


@runtime_checkable
class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for given text."""


@runtime_checkable
class SyncEmbedder(Protocol):
    def embed(self, text: str) -> list[float]:
        """Synchronous embedder (for tests or simple adapters)."""
