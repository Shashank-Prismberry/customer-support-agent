# Repository Instructions — Customer Support AI Orchestrator

## Project context

This repository implements Track 4: LangGraph AI Agent and Orchestration for a multi-tenant B2B Customer Support AI system.

Before making significant changes, read:

- `docs/IMPLEMENTATION_PLAN.md`
- `docs/PROGRESS.md`
- `docs/INTEGRATION_CONTRACT.md`, when available

The implementation plan is the architectural reference. The shared team contract is authoritative for external service interfaces and security rules.

## Architecture

The system consists of:

- Request Analyzer: identifies intent and quick/context/deep execution mode.
- Supervisor: coordinates execution and delegates to specialists.
- Triage Agent: handles support-ticket analysis and workflows.
- Knowledge Agent: handles company policies and documentation through RAG.
- Billing Agent: handles invoices and refunds through MCP.
- MCP integration: connects to externally implemented business tools.
- RAG integration: connects to the external knowledge retrieval service.
- Backend integration: retrieves and persists permanent conversation history.

Do not create separate agents for quick, context and deep execution modes.

Do not treat Triage as a catch-all for all requests that are not billing or knowledge-related.

The Supervisor controls specialist execution. Specialists must not freely invoke one another without explicit orchestration.

MCP owns business operations. RAG owns document retrieval. Backend owns permanent business and conversation persistence. This repository owns reasoning and orchestration.

## Engineering principles

- Keep code simple, modular and maintainable.
- Follow existing project conventions.
- Avoid unnecessary abstractions, design patterns and dependencies.
- Do not overengineer.
- Do not create unnecessary files or classes.
- Do not rewrite working code without a clear reason.
- Do not refactor unrelated modules during small tasks.
- Keep graph nodes focused and meaningful.
- Use Pydantic models and explicit types for important interfaces.
- Use async appropriately for network operations.
- Keep configuration centralized.
- Prefer small, independently testable changes.

## Security requirements

- Verify JWTs using PyJWT with HS256 pinned.
- Validate signature, expiry, issuer and audience.
- Never log raw bearer tokens.
- Never put raw JWTs in LLM prompts, messages or checkpointed AgentState.
- Forward bearer tokens to downstream MCP/RAG services only in Authorization headers through trusted request-scoped handling.
- Keep verified identity claims in user context.
- Never trust LLM-generated organization IDs, customer IDs or roles.
- Never make authorization decisions based on prompt instructions.
- Never bypass backend, MCP or RAG authorization.
- Never expose internal notes to customers.
- Never invent successful business-operation results.

## State and memory

Keep AgentState minimal and typed.

Backend conversation history and LangGraph checkpointing are separate responsibilities.

Backend stores permanent messages and summaries.

LangGraph checkpointer stores execution progress and HITL resumption state.

Do not treat thread_id as the complete conversation-memory architecture.

Do not checkpoint secrets or raw JWTs.

## External integrations

Do not invent external endpoint URLs, request schemas, response schemas or approval-token mechanisms.

Use the shared integration contract.

When an interface is not yet available, document the missing dependency and use a clearly identified mock for local development.

Do not make a mock appear to be a real external integration.

## Testing

Use pytest and pytest-asyncio where appropriate.

Test meaningful functionality and failure paths.

Use the exact deterministic identities from the shared team contract.

Mock external services in unit tests.

Do not claim tests passed unless they were actually executed.

Do not weaken security tests merely to make an implementation pass.

## Development workflow

Work on one small task at a time.

Before implementing:

1. Inspect the relevant code.
2. Read the applicable implementation-plan section.
3. Explain the proposed changes.
4. Identify affected files and assumptions.

After implementing:

1. Run relevant tests and checks.
2. Explain the files changed.
3. Report actual verification results.
4. Suggest a conventional commit message.
5. Stop and wait for the next instruction.

Never automatically commit, push, create a PR or move to the next roadmap task without approval.

The developer reviews and commits each task manually.