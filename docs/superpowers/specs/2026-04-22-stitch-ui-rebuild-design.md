# MindMirror Stitch UI High-Fidelity Rebuild Design

## Summary

This design rebuilds the MindMirror frontend around the provided Stitch "Inner Sanctuary AI" references while preserving the current backend and core user workflows. The result should feel like a new product shell with a new information architecture, but it should continue to run on the existing FastAPI application, existing authentication model, existing chat/session flows, existing essay workflows, and existing knowledge-base workflows.

The guiding constraint is: rebuild the experience, not the business core.

## Goals

- Rebuild the app to closely match the Stitch reference structure and visual language.
- Replace the current login screen with a combined landing-plus-auth entry experience.
- Reorganize the authenticated app around these views:
  - `dashboard`
  - `knowledge_base`
  - `reflections`
  - `ai_explorer`
  - `insights`
  - `timeline`
  - `settings`
- Keep the current backend and important flows largely unchanged.
- Add only small, read-only aggregation endpoints where the new views need them.
- Preserve full app operation during the migration instead of requiring a disruptive rewrite.

## Non-Goals

- No migration to a different frontend framework.
- No replacement of FastAPI with server-rendered page templates.
- No rewrite of retrieval, agent, embedding, upload, or authentication logic.
- No new write-heavy product features beyond what the current app already supports.
- No redesign of the vector-storage or persistence model for core workflows.

## Current Project Context

MindMirror currently operates as a single-page app with frontend state switching across these authenticated views:

- `dashboard`
- `knowledge`
- `essays`
- `chat`
- `settings`

The frontend is implemented in static assets under `frontend/`, with a large `index.html`, `script.js`, and `style.css`. The backend exposes APIs for:

- authentication
- daily quote
- chat and streaming chat
- session list and session detail
- essay list, upload, delete
- knowledge document list, upload, delete

This existing functional surface is sufficient to support a significant UI rebuild if the frontend shell is reorganized and a small amount of read-only aggregation is added.

## Product Direction

The Stitch references define a calm editorial product with a "digital sanctuary" tone:

- warm off-white surfaces
- large rounded containers
- generous whitespace
- serif-led editorial hierarchy
- soft tonal gradients and card layering
- deliberate content grouping instead of dense utility layouts

The rebuilt app should preserve MindMirror's reflective use case while translating the current functional UI into that calmer, more premium structure.

## Architecture Decision

The app will remain a single authenticated frontend shell after login. The redesign will not introduce a second web app, multipage backend rendering, or a new frontend stack. Instead, the current single-page architecture will be refactored into a clearer shell-based layout:

1. `landing/auth shell`
2. `authenticated stitch shell`
3. `feature views`

This gives the project a high-fidelity visual transplant while minimizing backend risk.

## Information Architecture Mapping

### Public Entry

#### `landing_page`

This replaces the current plain auth entry with a combined marketing and authentication experience. It includes:

- brand narrative
- product promise
- selected hero metrics or teaser insights
- clear login and register entry points

Authentication still uses the existing register/login APIs. This page is a presentation change, not a new auth system.

### Authenticated Views

#### `dashboard`

This remains the primary home view after login. It will be rebuilt as a Stitch-style overview page using existing data sources:

- daily quote
- recent essays
- recent sessions
- documents count
- essays count

The page changes structure and visual presentation but keeps the same underlying data dependencies.

#### `knowledge_base`

This is a direct evolution of the existing admin-only knowledge view. It keeps:

- admin visibility restrictions
- document upload
- upload progress and upload errors
- document listing
- document deletion

The view becomes a richer resource library surface with stronger metadata presentation and clearer content blocks.

#### `reflections`

This is the new product name for the current essays area. It keeps:

- essay upload
- upload progress and upload errors
- essay listing
- essay deletion
- launch analysis from an essay into chat

The page becomes a reflective archive rather than a utilitarian file list.

#### `ai_explorer`

This is the new product name for the current chat area. It keeps:

- session list
- session deletion
- streaming answers
- essay-bound analysis mode
- RAG source display
- prompt suggestions

The view is rebuilt as a more immersive workspace that visually matches the Stitch explorer layout.

#### `insights`

This is a new real page, not a placeholder. It provides derived summaries based on current user activity, using existing essays and sessions wherever possible. It should show:

- writing volume overview
- recent activity summaries
- repeated topics or phrases
- lightweight theme clustering
- top referenced essays or sessions

This page should rely on aggregation rather than new generation-heavy backend behavior.

#### `timeline`

This is also a new real page. It presents a chronological activity stream showing how the user's reflective work evolved over time. It should include:

- essay upload events
- session activity events
- knowledge-base upload or deletion events where relevant
- recent milestones and grouped dates

It is a read-only historical view built on top of existing records.

#### `settings`

This keeps the current purpose of the settings view:

- current account information
- role display
- system totals

The page is visually rebuilt but functionally conservative.

## Frontend Refactor Shape

The current frontend is too centralized for a full high-fidelity transplant. The redesign will keep the existing stack but reorganize responsibilities.

### Target Frontend Structure

- `frontend/index.html`
  - keeps a single root app mount
  - gains a clearer separation between public entry and authenticated shell
- `frontend/script.js`
  - keeps current API wiring and state model
  - is reorganized around shell state, view state, and derived data
- `frontend/style.css`
  - becomes the source of the Stitch visual system
  - defines tokens, layout primitives, card primitives, and view-specific styling

### Shell Responsibilities

#### Public shell

Responsible for:

- hero layout
- auth mode switch
- entry actions
- stitch-style marketing presentation

#### Authenticated shell

Responsible for:

- primary navigation
- page title and header frame
- global background treatment
- shared search and quick actions
- responsive page container rules

#### View modules

Each view should have a clearly bounded template region and its own loading logic, while still reusing shared helpers and the existing fetch methods where possible.

## API Strategy

Existing endpoints stay in place and keep their behavior. The redesign should continue to use:

- `POST /auth/login`
- `POST /auth/register`
- `GET /auth/me`
- `GET /daily-quote`
- `GET /sessions`
- `GET /sessions/{session_id}`
- `DELETE /sessions/{session_id}`
- `POST /chat`
- `POST /chat/stream`
- `GET /essays`
- `POST /essays/upload/stream`
- `DELETE /essays/{filename}`
- `GET /documents`
- `POST /documents/upload/stream`
- `DELETE /documents/{filename}`

### New Read-Only Endpoints

Two new aggregation endpoints should be added.

#### `GET /insights`

Purpose:

- power the new insights page without changing core storage or write flows

Suggested response content:

- total essays
- total sessions
- most recent activity timestamps
- top themes or keywords derived from essay titles, filenames, and session metadata
- rolling activity counts over recent periods
- light summary cards for frontend presentation

This endpoint should avoid introducing heavy AI generation in the request path. It should aggregate existing persisted data.

#### `GET /timeline`

Purpose:

- power the new timeline page as a unified chronological feed

Suggested response content:

- date-grouped activity items
- event type
- timestamp
- label
- optional metadata for related essay, session, or document

The endpoint should collect from existing essay, session, and document records. If document timestamps are unavailable in some legacy cases, the API may omit them or mark them as unknown instead of fabricating data.

## Data Mapping Details

### Dashboard

Use existing:

- `dailyQuote`
- `essays`
- `sessions`
- `documents`

Derived frontend values:

- recent reflections
- last session summary
- counts and ratios
- editorial hero cards

### Knowledge Base

Use existing:

- `documents`
- upload progress/error state

No backend behavior changes required beyond preserving the current admin-only guard.

### Reflections

Use existing:

- `essays`
- upload progress/error state
- active essay binding logic

The redesign may compute richer card summaries on the frontend, but the essay source of truth remains unchanged.

### AI Explorer

Use existing:

- `sessions`
- `messages`
- `activeEssayId`
- `activeEssayTitle`
- `analysisMode`
- chat streaming

The current essay-binding behavior must remain intact because it directly supports the product's dual-channel reflective analysis flow.

### Insights

Use existing and aggregated:

- essays list and essay metadata
- sessions list and session metadata
- session timestamps
- essay timestamps
- optional RAG metadata already attached to messages when available

This page should degrade gracefully if some metadata is incomplete.

### Timeline

Use existing and aggregated:

- essay upload timestamps
- session updated timestamps
- document uploaded timestamps when available

If a record lacks a timestamp, it should either be excluded from time-ordered placement or displayed in a low-confidence fallback group rather than breaking sort order.

## Visual System Requirements

The rebuild should closely follow the Stitch references without requiring Tailwind adoption.

### Typography

- editorial serif for major headings
- restrained sans-serif for body and UI
- large headline scale on landing and dashboard
- softer, spacious body copy rhythm

### Layout

- wide but bounded content frame
- generous spacing between major sections
- rounded primary surfaces
- layered cards with low-contrast depth
- responsive transitions from editorial desktop layouts to tighter mobile stacks

### Tone

- sanctuary-like, calm, premium
- warm background and low-saturation accent usage
- no generic dashboard appearance
- no harsh utility-first density

### Visual Fidelity Rule

When there is tension between matching the Stitch composition and preserving old markup, visual fidelity wins unless the change would break a core workflow. This project is explicitly a high-fidelity transplant, not a light re-skin.

## Error Handling

The redesign must keep backend error semantics stable even when the UI presentation changes.

### Auth Errors

- continue using current login/register failure handling
- restyle as integrated inline or card-state messaging where appropriate

### Upload Errors

- preserve current upload progress and per-file failure behavior
- present failures in Stitch-style status blocks instead of raw utility layouts

### Chat Errors

- preserve current stream interruption and model error handling
- keep the conversation usable after failures

### Aggregation Page Errors

For `insights` and `timeline`:

- failures should not block the rest of the application
- each page should show a local recoverable empty/error state
- retry should be view-local

## Compatibility Constraints

- Preserve the current auth token handling.
- Preserve current role-based gating for the knowledge base.
- Preserve essay-to-chat binding fields:
  - `active_essay_id`
  - `active_essay_title`
  - `analysis_mode`
- Preserve current upload endpoints and batch streaming semantics.
- Preserve current session list and session detail loading patterns.
- Do not remove or rename stable fields consumed by existing code unless a compatibility layer exists during migration.

## Testing Strategy

Testing must prove that the visual rebuild did not damage the product core.

### Backend Tests

Add or update tests for:

- `GET /insights` route definition and schema
- `GET /timeline` route definition and schema
- auth protection for both endpoints
- aggregation edge cases with sparse data

### Frontend Tests

Add or update tests for:

- landing/auth shell rendering
- authenticated navigation using the new Stitch view names
- admin-only knowledge base navigation behavior
- dashboard quote and overview regions
- reflections upload/list shell
- ai explorer layout shell
- insights and timeline view mounting

### Workflow Regression Tests

Verify the following still work:

- login
- register
- fetch current user
- fetch daily quote
- load sessions
- open a session
- send chat messages with stream handling
- bind an essay to a new chat session
- upload essays
- delete essays
- upload knowledge documents as admin
- delete knowledge documents as admin

## Implementation Phases

### Phase 1: Shell and Theme Foundation

- create the new design token system in CSS
- rebuild public landing/auth shell
- rebuild authenticated navigation shell
- map current views to the new IA labels

### Phase 2: Core View Transplant

- rebuild dashboard
- rebuild knowledge base
- rebuild reflections
- rebuild ai explorer
- rebuild settings

These pages should continue using existing APIs and behaviors.

### Phase 3: New Aggregation Views

- add `GET /insights`
- add `GET /timeline`
- build the insights page
- build the timeline page

### Phase 4: Stabilization

- improve responsive behavior
- harden empty states and error states
- expand regression coverage
- run full targeted verification

## Risks and Mitigations

### Risk: Frontend Centralization Makes the Rebuild Fragile

Mitigation:

- reorganize shell and view responsibilities before deep visual work
- keep API methods stable while moving layout concerns outward

### Risk: High Visual Fidelity Could Break Existing Interactions

Mitigation:

- preserve current action wiring and data fields
- verify each major workflow after each phase

### Risk: Timeline Data Quality May Be Uneven

Mitigation:

- treat timeline as best-effort aggregation
- omit unsupported legacy events rather than invent timestamps

### Risk: Insights Could Drift Into Heavy Computation

Mitigation:

- constrain the first version to lightweight aggregation and derived summaries
- avoid adding generation-heavy backend logic to the core request path

## Acceptance Criteria

The redesign is complete when:

- the app visually aligns with the Stitch references at a product-shell level
- login entry is replaced by a combined landing/auth page
- authenticated navigation uses the Stitch IA
- dashboard, knowledge base, reflections, ai explorer, insights, timeline, and settings all exist as coherent Stitch-style views
- existing core flows still function end to end
- new `insights` and `timeline` pages are genuinely usable
- regression tests cover the new shell and critical old workflows

## Final Decision

Proceed with a high-fidelity Stitch transplant of the frontend shell and page structure, while preserving the current backend behavior and limiting backend additions to lightweight read-only aggregation for the new insights and timeline views.
