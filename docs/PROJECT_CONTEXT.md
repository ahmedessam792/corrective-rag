# Project context

## Product

Corrective RAG is a single-user, local evidence-research web application. It supports persistent workspaces containing PDF and DOCX sources, bilingual English/Arabic questions, inspectable citations, one bounded corrective retrieval retry, evidence-aware partial answers, explicit contradictions, and refusal when support is insufficient.

## Confirmed boundaries

- Separate React frontend and FastAPI backend; no Gradio or Streamlit.
- Local machine only; no production deployment or authentication in the MVP.
- No automatic cloud fallback, external embeddings, telemetry containing document text, or web search.
- Optional on-demand OCR for scanned PDFs.
- Every released factual claim has validated application-controlled citations.
- Target machine: Windows 10, Intel i7-8850H, 32 GB RAM, NVIDIA Quadro P600 with 4 GB VRAM.

## Success

The project succeeds only if the frozen evaluation corpus shows the corrective workflow improves retrieval and reduces unsupported answers versus a matched ordinary-RAG baseline. UI completeness alone is not success.

