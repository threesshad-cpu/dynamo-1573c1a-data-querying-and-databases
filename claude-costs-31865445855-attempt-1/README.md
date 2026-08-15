# LLM usage and cost estimates

This artifact contains cost metadata only. It intentionally excludes prompts, model responses, task names, and source file paths.

- `summary.json`: estimated totals grouped by workflow stage, provider, model, and source.
- `records.jsonl`: one minimal record per captured model session/request or Harbor job.

Raw model session IDs are deliberately omitted. Harbor analysis records can represent multiple analyzer sessions, reflected by `session_count`.

The legacy `claude-costs-*` artifact name is retained for downstream compatibility. These are client/provider-reported estimates, not a reconciled provider invoice.
