# Product design

## Direction

A dark editorial research environment with warm evidence surfaces. The product is an adaptive workspace, not a chatbot or analytics dashboard.

## Information model

- Source rail: documents, processing state, upload, and source selection.
- Research canvas: questions, answers, claim-level citations, and correction trace.
- Evidence lens: selected passage, stable source location, surrounding context, and conflicts.

Desktop uses three adaptive regions; tablet collapses the evidence lens into a drawer; mobile uses a single-column flow with source and evidence sheets.

## Tokens

- Canvas `#0b0f0e`; surface `#111714`; raised `#18201d`; hairline `#29332f`.
- Text `#f1f4f1`; muted `#96a29c`; evidence paper `#f2efe7`; paper text `#222622`.
- Verified `#68d39b`; retrieval `#73b7e8`; correction `#d8b768`; unsupported `#df7373`.
- UI typography: Instrument Sans with system fallback. Reading typography: Source Serif 4 with Georgia fallback.

Motion explains state and respects `prefers-reduced-motion`. Focus is always visible; semantic colors never carry meaning alone.

