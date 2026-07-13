---
name: react-resizable-panels v4 API
description: The v4 package changed its export names and orientation prop — breaks silently if you use the old API.
---

## Rule
Use `Group`, `Panel`, `Separator` exports. The `orientation` prop replaces the old `direction` prop.

**Why:** v4 breaking change; old names (`PanelGroup`, `PanelResizeHandle`) no longer exist. Runtime error if used.

**How to apply:** Any resizable layout (research workspace, etc.) must import from the new names:
```tsx
import { Group, Panel, Separator } from "react-resizable-panels";
<Group orientation="horizontal">
  <Panel>…</Panel>
  <Separator />
  <Panel>…</Panel>
</Group>
```
