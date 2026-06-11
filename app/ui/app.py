"""The four-tab dashboard, each tab a view of the same run: Chat (ask + route),
Sources (last query's chunks), Guardrails (pass/block log from the trace bus), Eval
(metrics over a corpus folder). Gradio imports lazily so this module's data wiring
stays testable without it.

build_app takes the orchestrator + trace bus by injection, plus an optional
eval_fn(corpus_folder) -> list[EvalRow] so the UI never reaches into other layers.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.ui import format as fmt
from app.ui.theme import build_css, load_tokens

if TYPE_CHECKING:
    from lib.contracts import EvalRow, Orchestrator
    from lib.trace import TraceBus


def build_app(
    orchestrator: "Orchestrator",
    bus: "TraceBus",
    *,
    variant: str = "light",
    eval_fn: "Callable[[str], list[EvalRow]] | None" = None,
) -> Any:
    import gradio as gr

    css = build_css(load_tokens(), variant)
    with gr.Blocks(css=css, title="CHASSIS", analytics_enabled=False) as demo:
        gr.Markdown("# CHASSIS\nContracts-first multi-agent RAG — every layer made visible.")

        with gr.Tab("Chat"):
            question = gr.Textbox(label="Ask the documents", placeholder="What is this about?")
            route = gr.Markdown()
            answer = gr.Markdown()
        with gr.Tab("Sources"):
            sources = gr.Dataframe(headers=fmt.SOURCE_HEADERS, label="Last query's chunks")
        with gr.Tab("Guardrails"):
            guardrails = gr.Dataframe(headers=fmt.GUARDRAIL_HEADERS, label="Pass / block log")
        with gr.Tab("Eval"):
            corpus = gr.Textbox(label="Corpus folder", placeholder="/path/to/docs")
            run = gr.Button("Run eval")
            metrics = gr.Dataframe(headers=fmt.EVAL_BASE_HEADERS)

        def on_ask(text: str) -> tuple[str, str, list[list[str]], list[list[str]]]:
            result = orchestrator.handle(text)
            return (
                f"**route:** {result.route}",
                result.text or "(no answer)",
                fmt.source_rows(result),
                fmt.guardrail_rows(bus.recent()),
            )

        question.submit(on_ask, question, [route, answer, sources, guardrails])

        if eval_fn is not None:

            def on_eval(path: str) -> Any:
                headers, data = fmt.eval_table(eval_fn(path))
                return gr.Dataframe(value=data, headers=headers)

            run.click(on_eval, corpus, metrics)

    return demo
