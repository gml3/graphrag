"""A module containing run_workflow method definition."""

import logging
from typing import Any, cast

import pandas as pd

from callbacks.workflow_callbacks import WorkflowCallbacks
from config.models.chunking_config import ChunkStrategyType
from config.models.graph_rag_config import GraphRagConfig
from index.operations.chunk_text.chunk_text import chunk_text
from index.typing.context import PipelineRunContext
from index.typing.workflow import WorkflowFunctionOutput
from index.utils.hashing import gen_sha512_hash
from utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")
    documents = await load_table_from_storage("documents", context.output_storage)

    chunks = config.chunks

    output = create_base_text_units(
        documents,
        context.callbacks,
        chunks.group_by_columns,
        chunks.size,
        chunks.overlap,
        chunks.encoding_model,
        strategy=chunks.strategy,
    )

    await write_table_to_storage(output, "text_units", context.output_storage)

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=output)


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    group_by_columns: list[str],
    size: int,
    overlap: int,
    encoding_model: str,
    strategy: ChunkStrategyType,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    # 先按文档 ID 排序（保证每次运行结果一致）
    sort = documents.sort_values(by=["id"], ascending=[True])

    # 把每行的 id 和 text 捆绑成一个元组(doc_id, text)，存到新列 text_with_ids 里
    sort["text_with_ids"] = list(
        zip(*[sort[col] for col in ["id", "text"]], strict=True)
    )

    agg_dict = {"text_with_ids": list}
    if "metadata" in documents:
        agg_dict["metadata"] = "first"  # type: ignore

    # 在配置group_by_columns = ["id"] 意味着每篇文档独立切片，互不干扰。 
    # 但如果你把它改成比如 [author]，那同一个作者写的所有文章会先被拼接成一大段文字，然后再整体切片。这样可以让同一个作者的上下文信息在切片中更连贯。
    aggregated = (
        (
            sort.groupby(group_by_columns, sort=False)
            if len(group_by_columns) > 0
            else sort.groupby(lambda _x: True)
        )
        .agg(agg_dict)
        .reset_index()
    )
    aggregated.rename(columns={"text_with_ids": "texts"}, inplace=True)

    def chunker(row: pd.Series) -> Any:

        chunked = chunk_text(
            pd.DataFrame([row]).reset_index(drop=True),
            column="texts",
            size=size,
            overlap=overlap,
            encoding_model=encoding_model,
            strategy=strategy,
            callbacks=callbacks,
        )[0]

        row["chunks"] = chunked
        return row

    # Track progress of row-wise apply operation
    total_rows = len(aggregated)
    logger.info("Starting chunking process for %d documents", total_rows)

    def chunker_with_logging(row: pd.Series, row_index: int) -> Any:
        """Add logging to chunker execution."""
        result = chunker(row)
        logger.info("chunker progress:  %d/%d", row_index + 1, total_rows)
        return result

    aggregated = aggregated.apply(
        lambda row: chunker_with_logging(row, row.name), axis=1
    )

    aggregated = cast("pd.DataFrame", aggregated[[*group_by_columns, "chunks"]])
    aggregated = aggregated.explode("chunks")
    aggregated.rename(
        columns={
            "chunks": "chunk",
        },
        inplace=True,
    )
    aggregated["id"] = aggregated.apply(
        lambda row: gen_sha512_hash(row, ["chunk"]), axis=1
    )
    aggregated[["document_ids", "chunk", "n_tokens"]] = pd.DataFrame(
        aggregated["chunk"].tolist(), index=aggregated.index
    )
    # rename for downstream consumption
    aggregated.rename(columns={"chunk": "text"}, inplace=True)

    return cast(
        "pd.DataFrame", aggregated[aggregated["text"].notna()].reset_index(drop=True)
    )
