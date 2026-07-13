---
name: data-tsd-source hydration warning
description: React hydration mismatch on data-tsd-source attribute is cosmetic; caused by TanStack devtools SSR/client annotation difference.
---

## Rule
Ignore `data-tsd-source` hydration mismatch warnings. They are not app bugs.

**Why:** TanStack Start's devtools inject `data-tsd-source` annotations during SSR that differ from the client-side annotation (different line numbers after edits). This is a devtools artifact, not a real hydration bug. The app renders correctly.

**How to apply:** Do not attempt to fix this warning by wrapping components in `suppressHydrationWarning` or restructuring the root. It resolves itself after a full page reload in production.
