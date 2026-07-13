---
name: StatusPill null-safety
description: Status map lookups in primitives.tsx must always have a fallback to avoid Cannot read properties of undefined runtime errors.
---

## Rule
Any component that maps a `status` string to a style object must use `?? fallback` — never assume the incoming value is always a valid key.

**Why:** Components can receive status values from external data or loose type assertions. A missing map key returns `undefined`, causing the first property access to throw.

**How to apply:** Pattern used in `StatusPill` in `primitives.tsx`:
```tsx
const PILL_MAP: Record<string, { c: string; dot: string; t: string }> = { ... };
const map = PILL_MAP[status] ?? { c: "text-muted-foreground …", dot: "bg-muted-foreground", t: label ?? status };
```
Same pattern applies to any `Record<ChipStatus | StatusType, …>[value]` lookup.
