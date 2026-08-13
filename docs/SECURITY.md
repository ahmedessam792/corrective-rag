# Security and privacy

## Trust boundaries

Uploaded documents and all retrieved text are untrusted. They are evidence payloads, never instructions. The local browser and backend are trusted for the single-user MVP; Ollama is expected to bind to localhost.

## Controls

- Allow only PDF and DOCX by extension, MIME hint, and file signature.
- Enforce upload size and ZIP expansion/member limits before parsing DOCX.
- Generate storage names; never use a submitted path.
- Do not execute macros, links, attachments, or document instructions.
- Keep prompts separated into trusted policy and delimited evidence.
- Generate citation IDs in application code and reject unknown model-selected IDs.
- Avoid document text in ordinary logs and progress events.
- No cloud fallback, external telemetry, or network tools for the answer model.
- Bind development services to loopback by default.

## Deferred

Authentication, multi-user authorization, remote deployment hardening, antivirus integration, and encrypted-at-rest workspaces are outside the local MVP.

