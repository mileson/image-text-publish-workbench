# Source evidence contract

Save a JSON object with topic, questions, platforms and sources. Each source has id, platform, url, retrieved_at, title, body, tags, created_at, updated_at, unique_visitors, visits, likes, comments, saves, followers, evidence_paths, relevance_reason, authority_reason, freshness_reason, use_decision and rights. Unknown values are null. Metrics keep the raw display and scope, for example {"raw":"1.2k", "scope":"post likes"}. Do not guess unavailable fields.

Only actual opened sources may be marked verified. Keep platform limitations in findings.md. For each drafted factual claim record its supporting source IDs or the supplied material that supports it. A proposed title or hashtag is a suggestion, not an observed platform metric.

Private source captures, third-party images and transcripts belong in the task output directory, not this repository. Share only assets you may redistribute.
