"""Native Ref Plans registration: no journal I/O or remote writes."""
from pathlib import Path

from .schemas import WORKSPACE_SCHEMA
from .workspace import Workspace

GUIDANCE = """Ref Plans is a shared working document for substantial work, not a transcript
or memory archive. Load hermes-ref:workspace for the procedure. Bind a known relevant
ref directly; otherwise discover once and create a private outline only if needed.
Read before follow-ups and update the SAME ref with evidence before handover.
Never infer a project from a previous session or upload final answers as a fallback.
Advisory mode does not block execution. On Ref failure report once and continue
authorised work; reconcile uncertain writes with one exact-target read, never a
blind repeated Create. [ref-plan] requests the workflow; [no-ref] skips this turn.
Hard enforcement is opt-in after verifying the tool in a fresh session. No automatic
agents, sharing, approvals or tests. Finish with the working ref link when relevant.
"""


def register(ctx):
    workspace = Workspace(ctx)
    ctx.register_system_prompt_section('hermes-ref.guidance', GUIDANCE, max_chars=1200)
    ctx.register_middleware('tool_execution', workspace.execution)
    ctx.register_hook('pre_llm_call', workspace.before)
    ctx.register_hook('pre_tool_call', workspace.gate)
    ctx.register_hook('transform_llm_output', workspace.finish)
    ctx.register_hook('on_session_finalize', workspace.release)
    ctx.on_unload(workspace.close)
    ctx.register_skill(
        'workspace', Path(__file__).resolve().parent / 'skills' / 'workspace' / 'SKILL.md',
        description='Use when coordinating substantial work in Ref Plans.',
        frontmatter={'name': 'workspace', 'description': 'Use when coordinating substantial work in Ref Plans.'},
    )
    ctx.register_tool(name='ref_workspace', toolset='hermes_ref', schema=WORKSPACE_SCHEMA, handler=workspace.handle)