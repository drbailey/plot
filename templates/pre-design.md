# Pre-Design Document Template

This template defines the structure for a **pre-design document** — a concise summary of a plan intended for team review. It is generated alongside and derived from the detailed `plan.md`.

---

## Purpose

The detailed `plan.md` is the complete specification an executor needs to implement. The **pre-design** is what a team needs to evaluate the proposal: problem, solution, key decisions, and trade-offs — nothing more.

Target length: **1-3 pages** (roughly 500–1500 words, excluding diagrams).

## When to Generate

A `pre-design.md` file MUST be generated or regenerated:
- When `plan.md` is first created (Mode A Step A6 in `planning.md`)
- When `plan.md` is revised (Mode B Step B2 in `planning.md`)
- The pre-design lives alongside the plan: `{stories_dir}/{story}/story{n}/plan/pre-design.md`

## How to Generate

Read the full `plan.md` and distill it into the structure below. Every section should be **brief and decisive** — state what we are doing and why, not exhaustive detail on how.

Rules:
- Prefer tables and bullet lists over prose paragraphs
- One sentence per bullet; no multi-sentence bullets
- Include at most one diagram (reuse or simplify from `plan.md`)
- Link back to `plan.md` sections for detail rather than duplicating content
- Do not include implementation steps, file paths, or code snippets
- Write for an audience that understands the domain but has not read the detailed plan

---

## Document Structure

```markdown
# Pre-Design: {project name}

> **Status**: {draft | approved}
> **Plan revision**: {n}
> **Date**: {date}

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Proposed Solution](#proposed-solution)
3. [Architecture Overview](#architecture-overview)
4. [Key Design Decisions](#key-design-decisions)
5. [Scope and Phases](#scope-and-phases)
6. [Trade-offs and Risks](#trade-offs-and-risks)
7. [Open Questions](#open-questions)

---

## Problem Statement

{2-4 sentences. What problem are we solving? Why now? What does the current
state look like and why is it insufficient?}

## Proposed Solution

{3-5 sentences. What are we building? How does it solve the problem at a high
level? What is the end state?}

## Architecture Overview

{One simplified diagram (ASCII or mermaid) showing the major components and
their relationships. Reuse or simplify from plan.md.}

{Optional: 1-2 sentence caption explaining the diagram.}

## Key Design Decisions

{Table format. Each row is a decision that the team should evaluate.}

| # | Decision | Choice | Rationale | Alternatives Considered |
|---|----------|--------|-----------|------------------------|
| 1 | ... | ... | ... | ... |

## Scope and Phases

**In scope:**
- {bullet per major deliverable}

**Out of scope / deferred:**
- {bullet per excluded item}

**Phase breakdown** (if applicable):

| Phase | Description | Depends On |
|-------|-------------|------------|
| 1 | ... | -- |

## Trade-offs and Risks

{Top 5-7. Each a single bullet: the risk/trade-off and its mitigation or
acceptance rationale.}

- **{Risk name}:** {one sentence description}. Mitigation: {one sentence}.

## Open Questions

{Top 3-5 questions the team should discuss before approving. Remove section if none.}

1. {question}
2. {question}
```

---

## Style Guide

- **Tone:** Direct, professional, no filler
- **Length:** Each section should be scannable in under 30 seconds
- **Audience:** Senior engineers and technical leads who need to approve or reject the approach
- **Links:** Reference `plan.md` section headers for anyone who wants deeper detail (e.g., "See plan.md > Task Breakdown for full task list")
