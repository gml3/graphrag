"""Storage functions for the GraphRAG run module."""

import logging
from io import BytesIO

import pandas as pd

from storage.pipeline_storage import PipelineStorage

logger = logging.getLogger(__name__)


async def load_table_from_storage(name: str, storage: PipelineStorage) -> pd.DataFrame:
    """Load a parquet from the storage instance."""
    filename = f"{name}.parquet"
    if not await storage.has(filename):
        msg = f"Could not find {filename} in storage!"
        raise ValueError(msg)
    try:
        logger.info("reading table from storage: %s", filename)
        return pd.read_parquet(BytesIO(await storage.get(filename, as_bytes=True)))
    except Exception:
        logger.exception("error loading table from storage: %s", filename)
        raise


async def write_table_to_storage(
    table: pd.DataFrame, name: str, storage: PipelineStorage
) -> None:
    """Write a table to storage."""
    # Convert Arrow-backed types to standard Python types for Parquet compatibility
    for col in table.columns:
        if isinstance(table[col].dtype, pd.ArrowDtype):
            table[col] = table[col].astype(object)
        elif table[col].dtype == object:
            # Check cell-level ArrowStringArray/ArrowExtensionArray
            table[col] = table[col].apply(
                lambda x: list(x) if hasattr(x, '_pa_array') or type(x).__name__.startswith('Arrow') else x
            )
    await storage.set(f"{name}.parquet", table.to_parquet())


async def delete_table_from_storage(name: str, storage: PipelineStorage) -> None:
    """Delete a table to storage."""
    await storage.delete(f"{name}.parquet")


async def storage_has_table(name: str, storage: PipelineStorage) -> bool:
    """Check if a table exists in storage."""
    return await storage.has(f"{name}.parquet")
