# Bundled capability origins

The public research and image-production modules are self-contained adaptations of the author-owned local workflows, with private configuration and assets removed.

| Capability | Source workflow | Public integration |
|---|---|---|
| Image/text source and asset preparation | pose-photo-content-generator | Theme-driven source collection, optional user-gallery reference, generation prompt patterns and image_assets.py with its tests; no pose-specific default |
| General/video source research | prewriting-research-collector | Questions, original-source evidence, metadata, source assessment and recorded gaps |
| Video cover production | social-cover-generator | Content brief, composition/identity/details, serial aspect-ratio generation and visual QA |

Native image generation is supplied by the user's Agent. No model weights, provider credentials, browser login, private portraits, template library or author's other installed skills are bundled. The named upstream workflows are provenance, not install prerequisites. The image utility operates locally and does not generate images.

The video case records native image generation and the same cover-brief structure; the retained project brief does not itself record a Skill invocation name. Research history explicitly records the research collector. This distinction prevents inferring a tool call solely from the final image.
