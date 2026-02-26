"""A package containing all built-in workflow definitions."""

from index.workflows.factory import PipelineFactory

from index.workflows.load_input_documents import (
    run_workflow as run_load_input_documents,
)
from index.workflows.create_base_text_units import (
    run_workflow as run_create_base_text_units,
)
from index.workflows.create_communities import (
    run_workflow as run_create_communities,
)
from index.workflows.create_community_reports import (
    run_workflow as run_create_community_reports,
)
from index.workflows.create_final_documents import (
    run_workflow as run_create_final_documents,
)
from index.workflows.create_final_text_units import (
    run_workflow as run_create_final_text_units,
)
from index.workflows.extract_graph import (
    run_workflow as run_extract_graph,
)
from index.workflows.finalize_graph import (
    run_workflow as run_finalize_graph,
)
from index.workflows.generate_text_embeddings import (
    run_workflow as run_generate_text_embeddings,
)

# register all of our built-in workflows at once
PipelineFactory.register_all({
    "load_input_documents": run_load_input_documents,
    "create_base_text_units": run_create_base_text_units,
    "create_communities": run_create_communities,
    "create_community_reports": run_create_community_reports,
    "create_final_documents": run_create_final_documents,
    "create_final_text_units": run_create_final_text_units,
    "extract_graph": run_extract_graph,
    "finalize_graph": run_finalize_graph,
    "generate_text_embeddings": run_generate_text_embeddings,
})
