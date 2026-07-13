---
name: Theme system
description: Four professional dark themes managed via ThemeProvider; applied as data-theme attribute on html element.
---

## Rule
Theme changes are applied via `document.documentElement.setAttribute("data-theme", value)`. The default Titan Dark theme uses an empty string for the attribute.

**Why:** CSS custom property overrides in `styles.css` are scoped to `[data-theme="midnight"]`, `[data-theme="deep-blue"]`, `[data-theme="carbon"]`. The base `:root` block is the Titan Dark default.

**How to apply:**
- `ThemeProvider` lives at `src/components/titan/ThemeProvider.tsx`
- Wrap app in `<ThemeProvider>` (done in `__root.tsx` RootComponent)
- Use `useTheme()` hook anywhere theme switching is needed
- Persisted to `localStorage` key `titan_theme`
- Four themes: `titan-dark` | `midnight` | `deep-blue` | `carbon`
- All four define the full set of CSS custom properties (background, foreground, card, primary, sidebar, etc.)
- Theme switcher UI lives in AppShell topbar (Palette icon button)
