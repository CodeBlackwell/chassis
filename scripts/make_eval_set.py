"""Generate an eval seed set from a corpus.

  python scripts/make_eval_set.py --corpus <folder> [--n 10] [--use-llm] [--out eval/seed.jsonl]

Without --use-llm it runs offline with a degenerate question per chunk; with it,
the configured LLM writes a question + reference answer per chunk.
"""

import argparse
import json
import os

from app.eval.dataset import generate
from config.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--out", default="eval/seed.jsonl")
    parser.add_argument("--use-llm", action="store_true")
    args = parser.parse_args()

    llm = Settings.load(args.profile).build("llm") if args.use_llm else None
    rows = generate(args.corpus, args.n, llm)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as handle:
        for row in rows:
            record = {"question": row.question, "ground_truth": row.ground_truth}
            handle.write(json.dumps(record) + "\n")
    print(f"wrote {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
