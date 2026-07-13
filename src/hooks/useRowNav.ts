import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Roving-focus keyboard navigation for tabular / list rows.
 * ArrowUp/Down move focus, Home/End jump to ends, Enter triggers onActivate.
 */
export function useRowNav<T>(items: T[], onActivate?: (item: T, index: number) => void) {
  const [focused, setFocused] = useState(0);
  const refs = useRef<Array<HTMLElement | null>>([]);

  useEffect(() => {
    if (focused >= items.length) setFocused(Math.max(0, items.length - 1));
  }, [items.length, focused]);

  const setRowRef = useCallback(
    (i: number) => (el: HTMLElement | null) => {
      refs.current[i] = el;
    },
    []
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (items.length === 0) return;
      let next = focused;
      if (e.key === "ArrowDown") next = Math.min(items.length - 1, focused + 1);
      else if (e.key === "ArrowUp") next = Math.max(0, focused - 1);
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = items.length - 1;
      else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onActivate?.(items[focused], focused);
        return;
      } else return;
      e.preventDefault();
      setFocused(next);
      refs.current[next]?.focus();
    },
    [focused, items, onActivate]
  );

  return { focused, setFocused, setRowRef, onKeyDown };
}
