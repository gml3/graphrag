import logging
from typing import Any
import json
import pandas as pd

from callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from callbacks.workflow_callbacks import WorkflowCallbacks
from config.enums import IndexingMethod
from config.models.graph_rag_config import GraphRagConfig
from index.run.utils import create_run_context
from index.typing.context import PipelineRunContext
from index.typing.pipeline import Pipeline
from index.typing.pipeline_run_result import PipelineRunResult
from utils.api import create_cache_from_config, create_storage_from_config
from index.run.utils import create_callback_chain
from index.typing.pipeline_run_result import PipelineRunResult
from index.workflows.factory import PipelineFactory
from logger.standard_logging import init_loggers

logger = logging.getLogger(__name__)


async def build_index(
    config: GraphRagConfig,
    method: IndexingMethod | str = IndexingMethod.Standard,
    callbacks: list[WorkflowCallbacks] | None = None,
    verbose: bool = False,
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    method : IndexingMethod default=IndexingMethod.Standard
        Styling of indexing to perform (full LLM, NLP + LLM, etc.).
    callbacks : list[WorkflowCallbacks] | None default=None
        A list of callbacks to register.
    additional_context : dict[str, Any] | None default=None
        Additional context to pass to the pipeline run. This can be accessed in the pipeline state under the 'additional_context' key.
    input_documents : pd.DataFrame | None default=None.
        Override document loading and parsing and supply your own dataframe of documents to index.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    init_loggers(config=config, verbose=verbose)

    # Create callbacks for pipeline lifecycle events if provided
    workflow_callbacks = (create_callback_chain(callbacks) if callbacks else NoopWorkflowCallbacks())

    outputs: list[PipelineRunResult] = []

    logger.info("Initializing indexing pipeline...")

    pipeline = PipelineFactory.create_pipeline(method) # 

    root_dir = config.root_dir

    input_storage = create_storage_from_config(config.input.storage) # 拿到FilePipelineStorage存储对象
    output_storage = create_storage_from_config(config.output)  # 输出结果的存储
    cache = create_cache_from_config(config.cache, root_dir)    # LLM 缓存

    # load existing state in case any workflows are stateful
    state_json = await output_storage.get("context.json")   # 读取上次运行的状态
    state = json.loads(state_json) if state_json else {}    # 没有就是空字典

    logger.info("Running standard indexing.")

    # 这个函数没有读取任何文件内容，它只是把各种"工具"装进一个工具箱（PipelineRunContext），方便后续每个 workflow 使用
    context = create_run_context(
        input_storage=input_storage,         # 📂 "输入文件柜" — 知道去哪儿读原始文档
        output_storage=output_storage,       # 📂 "输出文件柜" — 知道把结果存到哪儿
        cache=cache,                         # 💾 "LLM 缓存"   — 避免重复调 API
        callbacks=callbacks,                 # 📢 "通知器"     — 报告进度
        state=state,                         # 📋 "状态记事本"  — 存临时信息
    )
    counter = 0
    for name, workflow_function in pipeline.run():
        context.callbacks.workflow_start(name, None)
        result = await workflow_function(config, context)
        print(result.result)
        counter += 1
        if counter > 1:
            break


if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    from config.load_config import load_config

    config = load_config(root_dir=Path("."))
    asyncio.run(build_index(config))