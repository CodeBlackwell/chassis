"""Theming: load the token set and render CSS custom properties for Gradio. The
default theme is METHODPROOF (SHOMEN light / KINMYAKU dark). Pure (no Gradio import),
so it tests offline. See docs/reference/stack-matrix.md (Theming) to swap.
"""

import json
from pathlib import Path
from typing import Any

_TOKENS_PATH = Path(__file__).parent / "tokens.json"


def load_tokens(path: str | None = None) -> dict[str, Any]:
    return json.loads(Path(path or _TOKENS_PATH).read_text())


def build_css(tokens: dict[str, Any], variant: str = "light") -> str:
    palette = tokens[variant]
    root_vars = "\n".join(f"  --{key}: {value};" for key, value in palette.items())
    font = tokens.get("font", {"body": "Inter", "mono": "IBM Plex Mono"})
    return f""":root {{
{root_vars}
  --font-body: "{font['body']}";
  --font-mono: "{font['mono']}";
}}
.gradio-container {{
  background: var(--bg) !important;
  color: var(--ink) !important;
  font-family: var(--font-body), system-ui, sans-serif;
}}
.gradio-container h1 {{ color: var(--accent); letter-spacing: 0.02em; }}
.gradio-container button {{ border-radius: var(--radius) !important; }}
.gradio-container table, .gradio-container .cell-wrap {{
  font-family: var(--font-mono), monospace;
}}
"""
