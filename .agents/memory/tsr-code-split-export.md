---
name: TanStack Router code-splitter export loss
description: Module-level exported constants from another file can be undefined when used inside a ?tsr-split=component chunk.
---

## Rule
Do not pass an imported module-level const as a prop to a component that has its own default for that value. Instead, drop the prop entirely and let the component fall back to its own default.

**Why:** TanStack Router's `?tsr-split=component` code-splitting can fail to carry over named exports from sibling modules at runtime, yielding `ReferenceError: X is not defined` even though the TypeScript compiles fine.

**How to apply:** If `SomeComponent` has `prop = DEFAULT_FROM_SAME_FILE` as its default param, do not write `<SomeComponent prop={IMPORTED_DEFAULT} />` from a route file — just write `<SomeComponent />` and let the component use its own default. 

Confirmed broken pattern:
```tsx
// design-system.tsx (route) — crashes at runtime
import { Timeline, SAMPLE_TIMELINE } from "../components/titan/Timeline";
<Timeline events={SAMPLE_TIMELINE.slice(0,6)} />  // SAMPLE_TIMELINE undefined
```

Fixed pattern:
```tsx
import { Timeline } from "../components/titan/Timeline";
<Timeline showFilters showGrouping={false} />  // uses internal default
```
