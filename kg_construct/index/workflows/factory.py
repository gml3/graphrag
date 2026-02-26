"""Encapsulates pipeline construction and selection."""

import logging
from typing import ClassVar

from config.enums import IndexingMethod
from config.models.graph_rag_config import GraphRagConfig
from index.typing.pipeline import Pipeline
from index.typing.workflow import WorkflowFunction

logger = logging.getLogger(__name__)


class PipelineFactory:
    """A factory class for workflow pipelines."""
    
    # init里面初始化了workflows，把所有的workflow function注册到这个字典里，key是workflow name，value是workflow function
    workflows: ClassVar[dict[str, WorkflowFunction]] = {}  
    # 61行初始化了pipelines，把所有的pipeline注册到这个字典里，key是pipeline name，value是list of workflow names that make up the pipeline
    pipelines: ClassVar[dict[str, list[str]]] = {}

    @classmethod
    def register(cls, name: str, workflow: WorkflowFunction):
        """Register a custom workflow function."""
        cls.workflows[name] = workflow

    @classmethod
    def register_all(cls, workflows: dict[str, WorkflowFunction]):
        """Register a dict of custom workflow functions."""
        for name, workflow in workflows.items():
            cls.register(name, workflow)

    @classmethod
    def register_pipeline(cls, name: str, workflows: list[str]):
        """Register a new pipeline method as a list of workflow names."""
        cls.pipelines[name] = workflows

    @classmethod
    def create_pipeline(
        cls,
        method: IndexingMethod | str = IndexingMethod.Standard,
    ) -> Pipeline:
        """Create a pipeline generator."""
        workflows = cls.pipelines.get(method, [])
        logger.info("Creating pipeline with workflows: %s", workflows)
        return Pipeline([(name, cls.workflows[name]) for name in workflows])


_standard_workflows = [
    "load_input_documents",
    "create_base_text_units",
    "create_final_documents",
    "extract_graph",
    "finalize_graph",
    "create_communities",
    "create_final_text_units",
    "create_community_reports",
    "generate_text_embeddings",
]

PipelineFactory.register_pipeline(IndexingMethod.Standard, [*_standard_workflows]) # 在 Python 里，凡是不缩进写在模块顶层的代码，在 import 的那个瞬间，就会立刻被执行！
