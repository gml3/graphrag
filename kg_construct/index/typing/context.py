"""A module containing the 'PipelineRunContext' models."""

from dataclasses import dataclass

from cache.pipeline_cache import PipelineCache
from callbacks.workflow_callbacks import WorkflowCallbacks
from index.typing.state import PipelineState
from index.typing.stats import PipelineRunStats
from storage.pipeline_storage import PipelineStorage


@dataclass
class PipelineRunContext:
    """Provides the context for the current pipeline run."""

    stats: PipelineRunStats             # 运行统计
    input_storage: PipelineStorage      # 输入存储（读原始文档用）
    "Storage for input documents."
    output_storage: PipelineStorage     # 输出存储（读写中间结果用）
    "Long-term storage for pipeline verbs to use. Items written here will be written to the storage provider."
    previous_storage: PipelineStorage   # 旧数据存储（增量更新用）
    "Storage for previous pipeline run when running in update mode."
    cache: PipelineCache                # LLM缓存
    "Cache instance for reading previous LLM responses."
    callbacks: WorkflowCallbacks        # 回调通知
    "Callbacks to be called during the pipeline run."
    state: PipelineState                # 状态字典
    "Arbitrary property bag for runtime state, persistent pre-computes, or experimental features."