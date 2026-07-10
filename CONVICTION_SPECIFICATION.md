# CONVICTION SPECIFICATION

Version : 1.0
Status  : ACTIVE DESIGN DOCUMENT

Purpose

This document defines the institutional decision philosophy of the trading system.

It specifies how conviction is formed, how evidence contributes to decisions, and which principles every future intelligence module must follow.

This document defines policy only.

It contains no implementation details, algorithms, or source code.

All future behavioral changes must be documented and approved here before implementation.



I completely agree.

In fact, I think **this document will become more valuable than thousands of lines of code.**

We've spent the last few weeks ensuring:

* We don't violate "One File = One Responsibility."
* We don't hardcode philosophy into modules.
* We don't redesign completed work.

Now we need to freeze the **decision philosophy** before we write the intelligence.


# SECTION 1

## Institutional Trading Philosophy

Not ORB philosophy.

Trading philosophy.

Example:

```text
Markets are probabilistic.

No single evidence source can justify a trade.

Conviction is produced by independent evidence agreeing.

Market participation is preferred over prediction.

The system adapts to market behaviour.

Risk is controlled before opportunity.
```

This becomes immutable.

---

# SECTION 2

## Decision Hierarchy

Exactly what we discussed.

```text
Market

↓

Sector

↓

Industry

↓

Theme

↓

Results

↓

News

↓

Institutional Flow

↓

Relative Strength

↓

Price Behaviour

↓

ORB

↓

Conviction

↓

Portfolio Risk

↓

Execution
```

This is frozen.

---

# SECTION 3

## Evidence Philosophy

Every provider must answer:

```text
1.

What objective facts did I observe?

2.

How strongly should those facts support the hypothesis?
```

Nothing more.

---

# SECTION 4

## Provider Classification

This is extremely important.

Example:

| Provider          | Type        | Mandatory | Influence Only | Lifecycle   |
| ----------------- | ----------- | --------- | -------------- | ----------- |
| Sector            | Structural  | Yes       | No             | Live        |
| Industry          | Structural  | Yes       | No             | Live        |
| Relative Strength | Momentum    | Yes       | No             | Live        |
| Theme             | Context     | Yes       | No             | Live        |
| Results           | Event       | No        | No             | Time Decay  |
| News              | Event       | No        | No             | Rapid Decay |
| Market Mood       | Environment | No        | Yes            | Live        |
| Breadth           | Environment | No        | Yes            | Session     |

This alone will guide years of development.

---

# SECTION 5

## Evidence Lifecycle

Exactly what you discovered.

Evidence doesn't disappear.

It loses value.

Example:

```text
News

★★★★★

↓

★★★★☆

↓

★★★☆☆

↓

Expired
```

Results

```text
Quarterly Results

↓

Very Strong

↓

Strong

↓

Medium

↓

Weak
```

Sector

```text
Always Live
```

---

# SECTION 6

## Confluence Philosophy

This is probably the most important section.

We agreed:

Conviction is NOT

```text
30

+

20

+

15

=

65
```

Instead:

```text
Strength

×

Agreement

×

Confidence

↓

Conviction
```

That is institutional thinking.

---

# SECTION 7

## Conflict Resolution

Example:

Market Mood says

Bearish.

Sector says

Strong.

Relative Strength says

Leader.

Should trade be rejected?

No.

Conviction decreases.

Exactly what we agreed.

---

# SECTION 8

## Conviction Output

The engine should eventually answer:

```text
How strong?

How reliable?

How aligned?

How complete?

Should capital be allocated?
```

Not simply:

```text
Score = 84
```

---

# SECTION 9

## Capital Allocation Philosophy

Future.

Not position sizing.

Only philosophy.

Example:

```text
Higher Conviction

↓

Eligible for larger allocation

Lower Conviction

↓

Eligible for reduced allocation

Weak Conviction

↓

No allocation
```

---

# SECTION 10

## Long-Term Expansion

Future modules.

```text
News

Macro

Global Markets

Bond Yields

Currency

FII

DII

Options Flow

Volatility

Sentiment

AI Analysis
```

All become evidence providers.

Nothing changes in architecture.

---

# I think one more section is absolutely essential

This came from one of your earliest principles, and I think it should become the core of the entire specification.

## SECTION 0 — Decision Principles

These are the rules that **no code is ever allowed to violate**.

For example:

1. **No single provider can approve a trade.**
2. **No single provider (except risk and execution safety) can reject a trade.**
3. **Evidence contributes; Conviction decides; Risk authorizes; Execution acts.**
4. **The market is observed, not predicted.**
5. **Every decision must be explainable from objective evidence.**
6. **The architecture may evolve; the philosophy must remain stable.**
7. **The system is designed to maximize expectancy, not win rate.**

---

## My recommendation

I recommend we **do not write a single additional line of Python** until this document is complete and approved.

We've reached the point where the project's limiting factor is no longer software engineering—it's decision science.

Once this specification is frozen, implementing the Conviction Engine, Evidence Validator, and every future intelligence provider becomes a process of translating documented policy into code rather than inventing behavior during development. I believe this document will become the most important artifact in the entire project after `PROJECT_BRAIN.md`.


As of 05/07/2026 

CONVICTION_SPECIFICATION.md

1. Purpose
2. Decision Principles
3. Institutional Trading Philosophy
4. Decision Hierarchy
5. Evidence Philosophy
6. Provider Classification
7. Evidence Lifecycle
8. Confluence Philosophy
9. Conflict Resolution
10. Conviction Output
11. Capital Allocation Philosophy
12. Future Expansion
13. Revision History