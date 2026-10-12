---
name: workbench-image-production
description: Optional native image and cover preparation for a publishing workbench, with source-preserving copies, prompt records and visual quality checks.
---

# Bundled image production capability

This package includes the production instructions and templates, not an image model, account or API key. Use the user's Agent's actual native image tool; read its current tool documentation. Reuse existing generated files and do not install a third-party paid image service silently. If generation is unavailable, return usable image prompts and missing-asset slots instead of claiming that files were generated.

1. Read the topic, source evidence, current content brief and existing asset paths. Choose reuse or generate according to the user's request. Reuse authorized assets by default when they are sufficient; the full-generation route produces the requested missing covers and inner pages.
2. Resolve the headline/composition, identity/asset route, and visual details from supplied answers. User delegation lets the Agent decide routine design choices without another interview. No person is the safe default when the task contains no authorized portrait; do not bundle or reconstruct private face libraries.
3. Give every reference an explicit role: edit target, identity, composition or factual UI/product evidence. Inspect reference files before generation. Real product screenshots and logos must retain factual appearance. Do not invent a UI feature to make a cover attractive.
4. Use references/image-prompts.md. Generate one asset at a time, saving actual tool receipts, prompts and original outputs under the task output directory. Retain originals; derived copies have distinct names. Stop repetitive retries and explain an unavailable tool or persistent failure.
5. Keep requested text exact. Verify spelling, faces, hands, geometry, readable hierarchy, subject visibility and cross-cover identity. Reject a result with incorrect text or invented product evidence. Review every requested image rather than treating a successful tool call as visual approval.
6. Image/text workbenches typically use 3:4 cover candidates and ordered inner pages. The video renderer has cover roles cover=3:4, bilibiliCover=4:3, horizontalCover=16:9. These are this workbench's media contracts, not universal current platform rules. Register only real files with matching roles; do not substitute one aspect ratio for another.
7. The bundled scripts/image_assets.py can report exact duplicates, make contact sheets and normalize copies without stretching. Read --help first. Strict normalization refuses a ratio mismatch; cropping/padding needs the user's chosen design route. This utility never calls an image model and is not a substitute for visual inspection.
8. Record each asset in assets/manifest.json with id, role, path, origin (provided/generated), source evidence, rights, prompt file, actual generation receipt, dimensions, sha256 and QA state. Use no credential values. Private assets and task manifests stay outside Git.
9. Feed verified paths into the parent's workbench input contract. Missing media must remain missing or an upload slot. Report generated counts, reused counts, failed items and whether research was partial. Nothing in this stage posts content.

## Topic-first image/text route

Decide the image plan from the user's topic, audience and format. Support tutorials, product introductions, travel notes, explainers and other content. Set the requested cover/inner-page count without a fixed pose or character preset. Reuse supplied material when requested, or create original images from the topic and supporting evidence.

Gallery mode is optional. Read the user-authorized gallery, preserve stable reference IDs, choose a layout/color/type route, and pass selected images as clearly labeled style references to the native generator. Replace old subject text, claims and branding with current content. Do not copy an unrelated scene or person merely because it appears in the gallery. Inspect every output for agreement with the brief.

## Video-cover route

Adapted from social-cover-generator. Build a factual content brief from the transcript, choose a clear composition and headline, then generate each requested role serially. A presenter frame is usable only when authorized for this task. Carry the selected layout and identity across aspect ratios; inspect clipping and title safety in every role. Never reuse a previous project's claim, money amount or portrait as a default.
