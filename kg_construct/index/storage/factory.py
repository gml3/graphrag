"""Factory functions for creating storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from config.enums import StorageType
from storage.file_pipeline_storage import FilePipelineStorage
from storage.memory_pipeline_storage import MemoryPipelineStorage

if TYPE_CHECKING:
    from collections.abc import Callable

    from storage.pipeline_storage import PipelineStorage


class StorageFactory:
    """A factory class for storage implementations."""

    _registry: ClassVar[dict[str, Callable[..., PipelineStorage]]] = {}

    @classmethod
    def register(
        cls, storage_type: str, creator: Callable[..., PipelineStorage]
    ) -> None:
        """Register a custom storage implementation."""
        cls._registry[storage_type] = creator

    @classmethod
    def create_storage(cls, storage_type: str, kwargs: dict) -> PipelineStorage:
        """Create a storage object from the provided type."""
        if storage_type not in cls._registry:
            msg = f"Unknown storage type: {storage_type}"
            raise ValueError(msg)
        return cls._registry[storage_type](**kwargs)

    @classmethod
    def get_storage_types(cls) -> list[str]:
        """Get the registered storage implementations."""
        return list(cls._registry.keys())

    @classmethod
    def is_supported_type(cls, storage_type: str) -> bool:
        """Check if the given storage type is supported."""
        return storage_type in cls._registry


StorageFactory.register(StorageType.file.value, FilePipelineStorage)
StorageFactory.register(StorageType.memory.value, MemoryPipelineStorage)
