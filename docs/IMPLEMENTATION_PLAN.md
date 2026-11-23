# Customer Support AI — LangGraph Orchestrator
## Implementation Plan

**Repository:** `customer-support-agent`  
**Component:** Track 4 — AI Agent & Orchestration  
**Technology:** Python, FastAPI, LangGraph, LangChain, Pydantic, MCP, RAG  
**Package manager:** uv  
**Architecture:** Modular monolithic application with a LangGraph orchestration workflow

---

# 1. Project Overview

This repository implements the AI reasoning and orchestration layer of a multi-tenant B2B Customer Support AI system.

The overall system consists of four independently developed components:

1. Backend and Database — Authentication, business data, tenant isolation and conversation persistence.
2. MCP Server — Exposes business operations such as ticket management and refunds.
3. RAG Service — Retrieves company policies, documentation and knowledge-base content.
4. LangGraph Orchestrator — Understands customer requests, coordinates agents and tools, manages workflows and generates responses.

Our repository is responsible for component 4.

## 1.1 Main objective

Build an AI support system capable of:

- Understanding incoming customer and staff requests.
- Identifying the intent and complexity of requests.
- Selecting the appropriate execution strategy.
- Coordinating specialist agents.
- Calling external MCP tools.
- Retrieving company knowledge through the RAG service.
- Retrieving relevant conversation history from the backend.
- Managing multi-step workflows.
- Supporting human-in-the-loop approval.
- Producing accurate responses grounded in actual tool and retrieval results.

The system must support multiple organizations and user roles while preserving the security boundaries defined by the shared team contract.

## 1.2 What this repository does NOT own

The orchestrator must not duplicate responsibilities belonging to other repositories.

| Responsibility | Owning component |
|---|---|
| User authentication and token issuance | Backend |
| PostgreSQL database and RLS | Backend |
| Ticket CRUD and ticket permissions | Backend/MCP |
| Invoice and refund execution | Backend/MCP |
| Audit logs | Backend |
| Document ingestion and embeddings | RAG |
| Vector search and document access filtering | RAG |
| Permanent conversation storage | Backend |
| Agent reasoning and workflow orchestration | This repository |
| LangGraph execution checkpointing | This repository |

MCP provides capabilities. Agents reason about domain-specific tasks. LangGraph coordinates their execution.

---

# 2. Architectural Decisions

These decisions are the current project baseline. Do not replace them with a different architecture without a clear technical reason and explicit approval.

## 2.1 Request Analyzer

The Request Analyzer is the initial request-understanding component.

It identifies two separate dimensions:

**A. Execution mode**

- `quick`
- `context`
- `deep`

**B. Request intent**

- `ticket`
- `knowledge`
- `billing`
- `general`

It may also identify:

- Whether conversation history is needed.
- Whether RAG retrieval is needed.
- Whether MCP tools are needed.
- Whether a workflow may require approval.

Example output:

```python
{
    "execution_mode": "deep",
    "intent": "billing",
    "requires_conversation_history": True,
    "requires_rag": True,
    "requires_mcp": True,
    "requires_approval": False,
    "reasoning": "The customer wants an invoice checked against the refund policy."
}
```

Execution modes:

**Quick:** The request can be answered using the current message and minimal context. Usually one direct response or one/few tool calls.

**Context:** The request requires previous conversation context or limited additional retrieval.

**Deep:** The request requires multiple dependent operations, multiple specialists, planning, business actions or possible approval.

Important:

- Execution mode is not a separate agent.
- Request intent is not execution complexity.
- A short refund request can be deep.
- A long informational question can still be quick.
- The Analyzer provides planning information, not authorization.
- The Analyzer must not decide whether a refund is permitted.

Implement the Analyzer as a lightweight, validated component. Use deterministic rules for straightforward cases where practical and structured LLM output where semantic understanding is needed.

Do not create three independent Quick, Context and Deep agents.

## 2.2 Supervisor

The Supervisor is the main orchestration component.

Responsibilities:

- Interpret the Analyzer's output.
- Decide which specialist is required.
- Decide the order of execution.
- Determine whether additional context or tools are needed.
- Coordinate multiple specialists when required.
- Evaluate specialist results.
- Handle missing information and clarification.
- Decide whether the workflow can finish or needs another step.
- Coordinate approval and graph resumption.
- Produce the final grounded response.

Use deterministic routing for clear cases and LLM-driven planning when the request requires more complex coordination.

The Supervisor must not perform every specialist's work itself.

It must not assume that every request needs all three specialist agents.

## 2.3 Specialist agents

### Triage Agent

Responsible for support-ticket understanding and ticket-related workflows.

Responsibilities:

- Understand unstructured customer complaints.
- Extract the actual problem and relevant details.
- Identify ticket category and suggested priority.
- Identify missing information.
- Ask for clarification when necessary.
- Prepare structured ticket creation requests.
- Retrieve and interpret existing ticket information.
- Help with ticket-related follow-up workflows.

Triage uses MCP ticket tools.

It is not a catch-all agent for non-billing and non-knowledge requests.

The current MCP contract does not provide a tool to update the category or priority of an existing ticket. Triage must not pretend that it can persist such changes.

### Knowledge Agent

Responsible for company documentation and knowledge-based questions.

Responsibilities:

- Understand knowledge-related questions.
- Retrieve relevant information through the RAG service.
- Answer using retrieved content.
- Include source references where available.
- Identify when retrieved information is insufficient.
- Avoid inventing policies or documentation.

Knowledge must use RAG for company-specific information.

It must not use RAG as a substitute for retrieving operational ticket or invoice data.

### Billing Agent

Responsible for invoice and refund workflows.

Responsibilities:

- Understand invoice and refund-related requests.
- Retrieve invoice information through MCP where supported.
- Evaluate available information against company policy retrieved through RAG when necessary.
- Prepare refund requests.
- Handle approval-dependent workflows.
- Execute refunds only through the approved MCP tool.
- Report actual backend results.

The backend remains authoritative for refund permissions, remaining balance, approval-token validation, idempotency and atomic execution.

## 2.4 Agent interaction model

The Supervisor controls agent execution.

Agents should not freely invoke one another without explicit orchestration.

The same specialist can handle both simple and complex requests.

For example:

- Quick invoice lookup: Billing Agent with one MCP call.
- Complex refund request: Supervisor coordinates Billing and Knowledge, potentially with approval.

A direct general response should also be possible without invoking a specialist.

---

# 3. Data and Context Architecture

There are four distinct information sources.

## 3.1 Identity and authorization context

Obtained from the verified JWT.

Required context:

- `user_id`
- `customer_id`
- `org_id`
- `role`
- `email`

Supported roles:

- `Org_Admin`
- `Support_Agent`
- `End_Customer`

The orchestrator must verify JWTs using PyJWT and pin the algorithm to HS256.

Validate the configured signature, expiration, issuer and audience.

Expected issuer: `support-ai-backend`

Expected audience: `support-ai-services`

The backend alone issues tokens.

Raw JWT handling:

- Never place a raw JWT in an LLM prompt.
- Never place a raw JWT in `messages`.
- Never place a raw JWT in checkpointed AgentState.
- Never log raw tokens.
- Forward the original bearer token to MCP and RAG using HTTP Authorization headers.
- Keep token forwarding in request-scoped integration handling or another trusted runtime mechanism that is not persisted in graph state.

The graph's user context contains verified identity claims, not the bearer token.

## 3.2 Conversation history

Permanent conversation history belongs to the backend.

The orchestrator should retrieve only relevant context for each request.

Possible strategy:

- Recent conversation messages.
- A compact conversation summary.
- Older relevant messages when needed.

Do not load unlimited history into every prompt.

Do not treat the LangGraph checkpoint as the complete conversation history.

The exact backend conversation APIs must be agreed upon with the backend developer. Do not invent endpoints or response schemas.

## 3.3 Operational business information

Retrieved through MCP.

Examples:

- Ticket details.
- Ticket searches.
- Ticket creation.
- Ticket status changes.
- Internal notes.
- Invoice and refund operations.

MCP is the source of truth for these operations.

## 3.4 Company policies and knowledge

Retrieved through RAG.

Examples:

- Refund policies.
- Cancellation policies.
- Product documentation.
- FAQs.
- Internal staff documentation.

RAG is the source of truth for company-specific knowledge.

Do not invent company policy when retrieval is unavailable or insufficient.

---

# 4. LangGraph Workflow

The workflow should be modular and understandable.

Conceptual flow:

```text
START
  |
Authentication / Request Context
  |
Load Relevant Conversation Context
  |
Request Analyzer
  |
Supervisor / Router
  |
  +---- Direct / Quick Handling
  |
  +---- Context-Based Handling
  |
  +---- Deep Orchestration
            |
            +---- Triage Agent
            |
            +---- Knowledge Agent
            |
            +---- Billing Agent
            |
            +---- MCP Tool Calls
            |
            +---- RAG Retrieval
            |
            +---- Human Approval
  |
Result Validation
  |
Response Generation
  |
Persist Conversation
  |
END
```

This is a logical workflow, not a requirement that every box becomes an independent LangGraph node.

Use a small number of meaningful nodes.

The implementation should avoid unnecessary nested graphs, multiple independent agent frameworks or excessive abstractions.

## 4.1 Shared AgentState

The state should contain the information required to coordinate execution.

Initial candidate fields:

- `messages`
- `user_context`
- `execution_mode`
- `intent`
- `active_agent`
- `execution_plan`
- `conversation_context`
- `retrieved_context`
- `tool_results`
- `approval_status`

Use appropriate TypedDict/Pydantic types and LangGraph reducers such as `add_messages` where appropriate.

This is a starting point, not a finalized schema.

Do not add fields without a clear purpose.

Never store the raw JWT or other secrets in AgentState.

## 4.2 Error handling

Handle expected downstream failures explicitly.

Shared error codes:

- `UNAUTHORIZED` — 401
- `FORBIDDEN` — 403
- `NOT_FOUND` — 404
- `VALIDATION_ERROR` — 422
- `CONFLICT` — 409
- `SERVICE_UNAVAILABLE` — 503

A tool failure must not be presented as a successful business operation.

Examples:

- A 403 from MCP means the requested operation was not authorized.
- A 404 should not cause the agent to invent a record.
- A 503 should be communicated as temporary service unavailability.
- A timeout must not be interpreted as successful execution.

Do not retry non-idempotent operations blindly.

---

# 5. MCP Integration

Pulkit's MCP service exposes the following canonical tools:

| Tool | Purpose |
|---|---|
| `get_ticket_details` | Retrieve ticket details |
| `search_tickets` | Search tickets |
| `create_ticket` | Create a support ticket |
| `update_ticket_status` | Change ticket status |
| `add_internal_note` | Add a staff-only internal note |
| `issue_refund` | Execute a refund |

The orchestrator should connect to the MCP server and make the exposed tools available to the appropriate agents.

Use the agreed MCP transport. The project integration brief specifies Streamable HTTP, but confirm the actual server endpoint and SDK compatibility before implementation.

Do not duplicate the implementation of these tools.

## 5.1 Important refund rules

The shared contract specifies:

- Only `Org_Admin` can issue refunds.
- Refunds above $100 require an approval token.
- Approval tokens bind invoice, amount, organization and approver.
- Tokens have a 15-minute lifetime and are single-use.
- Refund amount cannot exceed remaining invoice balance.
- Idempotency keys prevent duplicate execution.
- Invoice update and audit log insertion are atomic.

For a refund above $100:

1. Prepare and validate the proposed request.
2. Request human approval through LangGraph HITL.
3. Resume the workflow after approval.
4. Obtain the appropriate approval token through the agreed backend mechanism.
5. Invoke `issue_refund`.
6. Report the actual result.

The exact approval-token issuance interface is not fully defined in the current contract. Coordinate with the backend developer rather than inventing an endpoint or generating tokens in the agent service.

For retries, preserve the original idempotency key. Backend idempotency must prevent duplicate refunds.

---

# 6. RAG Integration

The Knowledge Agent communicates with Akshit's RAG service.

The RAG service is responsible for:

- Verifying the bearer token.
- Deriving organization and access permissions.
- Filtering by tenant and allowed access level before retrieval.
- Returning relevant document chunks.

Access-level rules:

| Role | Permitted access |
|---|---|
| End_Customer | public |
| Support_Agent | public, internal_staff |
| Org_Admin | public, internal_staff, admin_only |

The RAG service must filter using:

```sql
WHERE org_id = $1
AND access_level = ANY($2)
```

Filtering after retrieval in Python is prohibited.

The orchestrator must not independently override access levels or trust an LLM's requested access tier.

The exact RAG endpoint, request schema and response schema must be agreed with the RAG developer.

Prefer preserving source metadata such as document IDs and titles so the Knowledge Agent can provide grounded answers.

---

# 7. Conversation Memory and Checkpointing

These are two different persistence responsibilities.

## Backend

Stores:

- Permanent conversation messages.
- Conversation summaries.
- Conversation ownership and tenant association.
- Other persistent business records.

## LangGraph checkpointer

Stores:

- Graph execution progress.
- Intermediate state.
- Pending workflow state.
- HITL interruption and resumption information.

Use the conversation ID or another stable execution identifier as the graph thread identifier, following the agreed backend integration design.

Do not assume that `thread_id` alone solves long-term memory.

Start with an in-memory checkpointer during local development.

Introduce a persistent checkpointer when the database and deployment integration are ready.

Never checkpoint secrets or raw bearer tokens.

---

# 8. Proposed Repository Structure

```text
customer-support-agent/
│
├── src/
│   └── support_agent/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── dependencies.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── security.py
│       │   └── logging.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   ├── responses.py
│       │   └── context.py
│       │
│       ├── analyzer/
│       │   ├── __init__.py
│       │   └── request_analyzer.py
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py
│       │   ├── nodes.py
│       │   ├── routing.py
│       │   └── workflow.py
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── supervisor.py
│       │   ├── triage.py
│       │   ├── knowledge.py
│       │   └── billing.py
│       │
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── supervisor.py
│       │   ├── triage.py
│       │   ├── knowledge.py
│       │   └── billing.py
│       │
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── mcp/
│       │   │   ├── __init__.py
│       │   │   ├── client.py
│       │   │   └── tools.py
│       │   │
│       │   ├── rag/
│       │   │   ├── __init__.py
│       │   │   └── client.py
│       │   │
│       │   └── backend/
│       │       ├── __init__.py
│       │       └── conversation_client.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── conversation.py
│       │   └── approval.py
│       │
│       └── persistence/
│           ├── __init__.py
│           └── checkpointer.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_security.py
│   ├── test_analyzer.py
│   ├── test_routing.py
│   ├── test_triage.py
│   ├── test_knowledge.py
│   ├── test_billing.py
│   ├── test_integrations.py
│   └── test_workflow.py
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROGRESS.md
│   └── INTEGRATION_CONTRACT.md
│
├── .github/
│   ├── copilot-instructions.md
│   └── instructions/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

Do not create every file with placeholder code immediately. Introduce modules when their corresponding task begins.

---

# 9. Technology and Dependencies

Use:

- Python 3.10+ initially, subject to team environment compatibility.
- uv for dependency and environment management.
- FastAPI for the service API.
- LangGraph for orchestration.
- LangChain for model and tool integration where useful.
- Pydantic for schemas and validation.
- PyJWT for JWT verification.
- httpx for HTTP integrations.
- LangChain MCP Adapters or the agreed MCP SDK for MCP connectivity.
- pytest and pytest-asyncio for testing.

Potential initial dependencies:

```bash
uv add fastapi "uvicorn[standard]"
uv add langgraph langchain langchain-openai
uv add pydantic pydantic-settings
uv add pyjwt httpx
uv add pytest pytest-asyncio
```

Add MCP, checkpointing and other dependencies only when their implementation is about to begin and their compatibility has been checked.

Do not add unnecessary libraries.

---

# 10. Environment Configuration

Initial `.env.example`:

```env
APP_NAME=customer-support-agent
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8003

JWT_SECRET_KEY=

JWT_ISSUER=support-ai-backend
JWT_AUDIENCE=support-ai-services

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

MCP_SERVER_URL=
RAG_SERVICE_URL=
BACKEND_API_URL=

CHECKPOINT_DATABASE_URL=
```

The port is provisional. Confirm the actual service port with the team.

Do not commit `.env`, credentials, tokens or API keys.

All configuration must be accessed through a central settings module.

---

# 11. Implementation Roadmap and Commit Strategy

Development must be divided into small, independently verifiable tasks.

Do not implement all phases in one Copilot operation.

## Phase 0 — Repository initialization

**Task 0.1:** Inspect the existing workspace and Git state.

**Task 0.2:** Initialize the Python package using uv.

**Task 0.3:** Create the initial directory structure.

**Task 0.4:** Add README, `.gitignore`, `.env.example` and project documentation placeholders.

**Verification:**

- Package initializes successfully.
- Directory structure is correct.
- No secrets are committed.
- `uv sync` succeeds.

Suggested commit:

`chore: initialize customer support agent repository`

## Phase 1 — Application foundation

**Task 1.1:** Create central settings configuration.

**Task 1.2:** Create the FastAPI application entry point.

**Task 1.3:** Add health endpoint.

**Task 1.4:** Add initial request and response schemas.

**Task 1.5:** Add application-level error handling.

**Verification:**

- Application starts.
- `/health` returns a valid response.
- Configuration loads correctly.
- API validation works.
- Tests pass.

Suggested commit:

`feat: add FastAPI application foundation`

## Phase 2 — Authentication and context

**Task 2.1:** Implement JWT verification.

**Task 2.2:** Validate signature, algorithm, expiration, issuer and audience.

**Task 2.3:** Create the authenticated user context model.

**Task 2.4:** Add FastAPI authentication dependency.

**Task 2.5:** Add tests for valid and invalid identities.

**Verification:**

- Valid tokens are accepted.
- Invalid and expired tokens are rejected.
- Role and organization claims are extracted correctly.
- Raw tokens are not logged or included in graph state.

Suggested commit:

`feat: add JWT authentication and user context`

## Phase 3 — LangGraph foundation

**Task 3.1:** Define the initial AgentState.

**Task 3.2:** Implement a minimal graph.

**Task 3.3:** Add a basic request node.

**Task 3.4:** Compile the graph.

**Task 3.5:** Add graph execution tests.

**Verification:**

- Graph compiles.
- State is passed and updated correctly.
- A basic request can enter and exit the graph.
- No unnecessary graph complexity is introduced.

Suggested commit:

`feat: establish LangGraph workflow foundation`

## Phase 4 — Request Analyzer

**Task 4.1:** Define RequestAnalysis Pydantic schema.

**Task 4.2:** Implement intent classification.

**Task 4.3:** Implement quick/context/deep classification.

**Task 4.4:** Add validation and safe fallback behaviour.

**Task 4.5:** Add analyzer tests.

**Verification:**

Test at least:

- Simple ticket status lookup.
- Historical conversation question.
- Refund request.
- Company policy question.
- General conversation.
- Ambiguous request.

Suggested commit:

`feat: add request analysis and execution classification`

## Phase 5 — Routing and Supervisor

**Task 5.1:** Implement deterministic routing for clear requests.

**Task 5.2:** Implement Supervisor decision logic.

**Task 5.3:** Define specialist delegation interfaces.

**Task 5.4:** Add routing and orchestration tests.

**Verification:**

- Ticket requests reach Triage.
- Knowledge requests reach Knowledge.
- Billing requests reach Billing.
- General requests can be handled directly.
- Complex requests can involve multiple specialists.
- No unnecessary specialist calls occur.

Suggested commit:

`feat: add supervisor and specialist routing`

## Phase 6 — External integrations

**Task 6.1:** Confirm MCP transport and connection details.

**Task 6.2:** Implement MCP client lifecycle.

**Task 6.3:** Load and expose the six canonical MCP tools.

**Task 6.4:** Implement the RAG HTTP client.

**Task 6.5:** Implement backend conversation API client after its contract is agreed.

**Task 6.6:** Add mock integrations for independent local development.

**Verification:**

- MCP tools are discovered from the real server.
- RAG requests include the bearer token in the Authorization header.
- MCP requests include the bearer token in the Authorization header.
- Tokens are not included in prompts or checkpointed state.
- Mock and real clients follow compatible interfaces.
- External errors are handled safely.

Suggested commits:

`feat: add MCP integration`

`feat: add RAG and backend integrations`

## Phase 7 — Specialist agents

**Task 7.1:** Implement Triage Agent.

**Task 7.2:** Implement Knowledge Agent.

**Task 7.3:** Implement Billing Agent.

**Task 7.4:** Connect specialists to the graph.

**Task 7.5:** Add specialist tests.

**Verification:**

- Triage prepares valid ticket operations.
- Knowledge answers using retrieved content.
- Billing uses actual invoice data and appropriate policy information.
- Specialists do not invent tool results.
- Specialists do not bypass backend authorization.

Suggested commit:

`feat: implement ticket triage agent`

`feat: implement knowledge agent`

`feat: implement billing agent`

## Phase 8 — Conversation context and memory

**Task 8.1:** Define conversation context schemas.

**Task 8.2:** Implement history retrieval.

**Task 8.3:** Implement bounded context preparation.

**Task 8.4:** Support summary and relevant historical message usage.

**Task 8.5:** Implement conversation persistence integration.

**Verification:**

- Relevant previous messages can influence responses.
- Entire conversation history is not blindly loaded.
- Authoritative business information is retrieved from its source.
- Graph state and backend transcript remain separate.

Suggested commit:

`feat: add conversation context management`

## Phase 9 — Human-in-the-loop and approval

**Task 9.1:** Define approval workflow state.

**Task 9.2:** Implement LangGraph interruption.

**Task 9.3:** Implement approval resumption.

**Task 9.4:** Integrate the agreed backend approval-token mechanism.

**Task 9.5:** Test rejection, expiry and successful approval paths.

**Verification:**

- Refunds above $100 cannot proceed without approval.
- Workflow pauses before execution.
- Rejected and expired approvals do not execute refunds.
- Resume does not accidentally repeat earlier operations.
- Backend validates the approval token.
- Idempotency key is preserved across retries.

Suggested commit:

`feat: add human approval workflow`

## Phase 10 — Integration, security and testing

**Task 10.1:** Add end-to-end graph tests using mocks.

**Task 10.2:** Add real-service integration tests when dependencies are available.

**Task 10.3:** Verify error handling.

**Task 10.4:** Verify tenant and role boundaries through downstream responses.

**Task 10.5:** Test conversation continuity and checkpoint resumption.

**Task 10.6:** Add structured logging and observability.

**Verification:**

- All tests pass.
- No raw JWT leakage.
- Unauthorized tool calls fail safely.
- Cross-tenant data is never exposed.
- Tool failures are not represented as successful operations.
- Approval workflows resume correctly.

Suggested commit:

`test: add orchestration integration and security tests`

## Phase 11 — Final documentation and integration

**Task 11.1:** Document architecture.

**Task 11.2:** Document environment variables.

**Task 11.3:** Document service startup.

**Task 11.4:** Document MCP and RAG dependencies.

**Task 11.5:** Document sample workflows and known limitations.

Suggested commit:

`docs: document orchestrator setup and integration`

---

# 12. Shared Team Contract Constraints

Use the shared team contract v2.3 as the authoritative source for the following.

## Roles

- `Org_Admin`
- `Support_Agent`
- `End_Customer`

## Ticket status

- `open`
- `in_progress`
- `resolved`
- `closed`

## Priority

- `low`
- `medium`
- `high`
- `urgent`

## Categories

- `billing`
- `technical`
- `account`
- `general`

## Invoice status

- `paid`
- `pending`
- `refunded`
- `partially_refunded`

## Standard error codes

- `UNAUTHORIZED`
- `FORBIDDEN`
- `NOT_FOUND`
- `VALIDATION_ERROR`
- `CONFLICT`
- `SERVICE_UNAVAILABLE`

## Deterministic test identities

Use the identities defined in Shared Team Contract v2.3:

- Alice: Org A, Org_Admin.
- Bob: Org A, Support_Agent.
- Charlie: Org A, End_Customer.
- Dave: Org B, Org_Admin.

Use their exact UUIDs from the shared contract. Do not invent alternative test identities.

## Important restrictions

- Never trust an organization ID or role supplied by the LLM.
- Never bypass downstream authorization.
- Never expose internal notes to customers.
- Never invent invoice, ticket or refund results.
- Never expose one tenant's information to another tenant.
- Never use RAG results without respecting the access restrictions.
- Never execute refunds through anything other than the approved backend/MCP mechanism.

---

# 13. Development and Git Workflow

Development must follow a small-task workflow.

For every task:

1. Read the relevant implementation-plan section.
2. Inspect the current repository and existing code.
3. Identify the files that need to change.
4. Explain the proposed implementation briefly.
5. Implement only the requested task.
6. Run relevant tests and checks.
7. Inspect the final changes.
8. Explain what was implemented and what remains.
9. Wait for developer verification before moving to the next task.

Do not automatically commit or push.

The developer will review and create commits and pull requests manually.

Use conventional commit messages:

- `chore: ...`
- `feat: ...`
- `fix: ...`
- `test: ...`
- `docs: ...`
- `refactor: ...`

Each PR should represent one logically complete, independently reviewable change.

Do not mix unrelated tasks into a single PR.

---

# 14. Definition of Done

A task is complete only when:

- The requested functionality is implemented.
- The implementation follows the agreed architecture.
- Relevant tests pass.
- No secrets or credentials are committed.
- Error handling is appropriate.
- No unrelated files or features were changed.
- The code is understandable and maintainable.
- The task's acceptance criteria are satisfied.
- Documentation is updated when necessary.

The project is considered ready for integration when the complete graph can handle representative ticket, knowledge, billing, context-dependent and approval-dependent workflows using the actual downstream services.

---

# 15. Known Open Integration Questions

Do not invent answers to these questions. Record them and coordinate with the relevant team member.

1. Exact MCP Streamable HTTP endpoint and authentication handshake.
2. MCP SDK and LangChain MCP adapter versions compatible with the server.
3. Exact RAG endpoint, request schema and response schema.
4. Whether RAG returns document IDs, titles and source metadata.
5. Backend API for retrieving conversation messages and summaries.
6. Backend API for persisting new conversation messages and summaries.
7. How conversation IDs are created and associated with authenticated users.
8. How the refund approval token is issued after human approval.
9. How approval decisions are delivered to the graph for resumption.
10. Final orchestrator service port and deployment configuration.
11. Persistent LangGraph checkpoint storage and lifecycle.

Until these interfaces are confirmed, use mock clients and explicit configuration placeholders rather than fabricated APIs.

---

# Final Development Principle

Build a working, understandable system incrementally.

Prefer simple, explicit code over unnecessary abstractions.

Use LangGraph where stateful orchestration, conditional routing, multi-step workflows and interruption/resumption provide actual value.

Do not turn every function into an agent or every operation into a separate graph node.

Preserve the boundaries between the orchestrator, MCP, RAG and backend.

Implement, test, review, commit and integrate one small task at a time.