# Spec Writer Agent

## Overview
A skill/agent that transforms feature/problem descriptions into structured specifications that can be consumed by an Implementation Agent.

## Workflow

```
User Input → Spec Writer Agent → Structured Spec → Implementation Agent → TDD Agents → Implementation
```

## Spec Structure

### 1. Problem Statement
- What problem are we solving?
- Who is affected?
- What's the current pain point?

### 2. Goals & Success Criteria
- What does success look like?
- How will we measure it?
- What are the non-negotiables?

### 3. Requirements
**Functional:**
- What should the system do?
- User stories / use cases
- Input/output behavior

**Non-Functional:**
- Performance requirements
- Security considerations
- Scalability needs

### 4. Technical Design
- Architecture overview
- Component diagram (if applicable)
- Data model changes
- API specifications (if applicable)
- Dependencies (internal/external)

### 5. Edge Cases & Error Handling
- What can go wrong?
- How should errors be handled?
- What are the boundary conditions?

### 6. Testing Strategy
- Unit test scenarios
- Integration test points
- Manual QA checklist
- Performance testing requirements

### 7. Out of Scope
- What are we NOT doing?
- Future considerations

### 8. Implementation Notes
- Suggested approach
- Known constraints
- Risks & mitigations
- Timeline estimates (optional)

## Technical Design

### Spec Storage Format
Store specs as structured JSON/YAML for programmatic consumption:

```json
{
  "id": "uuid",
  "problem_statement": "...",
  "goals": [...],
  "requirements": {
    "functional": [...],
    "non_functional": [...]
  },
  "technical_design": {...},
  "testing_strategy": {...}
}
```

### Agent Responsibilities
- Parse user input
- Identify gaps in requirements
- Ask clarifying questions (via AskUserQuestion)
- Generate the structured spec
- Save to WIP directory

### Implementation Agent Integration
- Reads the spec JSON
- Maps requirements to test cases
- Spawns TDD agents per requirement
- Tracks progress against spec

### Shared Context
Both agents need access to:
- The spec file
- Current codebase state
- Existing tests
- Git history (for context)
