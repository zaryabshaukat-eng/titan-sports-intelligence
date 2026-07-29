# Phase 3.1: Frontend API Foundation

All browser API access lives in `src/api`. `client.ts` reads `VITE_API_BASE_URL` and falls back to `http://localhost:8000/api/v1` for local development. It uses Fetch with the TITAN v1 response-envelope header, timeouts, caller cancellation, safe JSON parsing, and the normalized `ApiError` model.

Feature modules contain no React code. They expose typed functions for one backend capability and return unwrapped data. Shared transport and domain contracts are in `src/types/api.ts` and `src/types/domain.ts`; add or amend those contracts rather than duplicating interfaces in pages.

TanStack Query hooks are in `src/hooks`. Each provides a query-options factory alongside the hook so a future route loader, prefetch operation, or component uses the same query key and request function.

To add a capability:

1. Add shared response/request types under `src/types`.
2. Add a focused `src/api/<feature>.ts` module using `apiClient`.
3. Add stable keys to `src/api/query-keys.ts` and a matching `src/hooks/use<Feature>.ts` hook.
4. Keep components free of direct `fetch` calls and import only the hook or query options they need.

`dashboardApi.get` deliberately targets the Phase 3.2 dashboard read model; it is not imported by the current UI and must not be used until that backend endpoint exists.
