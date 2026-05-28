# Product

## Register

product

## Users

The service owner: a solo operator who built and runs the Rubifo Rubika forwarding bot. Opens the admin panel to check revenue, monitor active subscriptions, inspect route health, review logs when something breaks, and adjust bot settings. Persian-speaking, technically fluent, works alone. Needs to get in and out quickly.

## Product Purpose

Rubifo is an automated Rubika channel forwarding service. Users subscribe to a bot that monitors source channels and forwards posts to destination channels on a schedule. The admin panel is the operator's control room: user management, subscription status, transaction history, route monitoring, performance metrics, system settings.

## Brand Personality

Controlled, precise, unhurried. Three words: confident, dense, legible.

## Anti-references

- Bootstrap / Flat UI palette (#3498db blue, #2c3e50 sidebar) — what the current version looks like; avoid entirely
- Generic SaaS dashboards with identical stat cards, gradient headers, and teal accents
- Neon/dark hacker aesthetic — not the register for this audience

## Design Principles

1. **Information before decoration** — every visual element earns its place by helping the operator read state faster
2. **Operator trust** — the interface communicates reliability; nothing should look playful or fragile
3. **RTL-ready density** — Persian text is present in data (amounts in تومان, channel names); layout must tolerate mixed directionality without breaking
4. **No learning curve** — the operator is the only user; the interface assumes fluency, not onboarding
5. **Calm authority** — Stripe-dashboard confidence: neutral palette, tight spacing, hierarchy through weight not color

## Accessibility & Inclusion

WCAG AA minimum. No known reduced-motion requirement. Color-blind-safe status indicators (badge colors must not rely on hue alone).
