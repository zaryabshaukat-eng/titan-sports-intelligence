import { useState, useMemo, useCallback } from "react";
import {
  ChevronUp, ChevronDown, ChevronsUpDown, Search, Download,
  ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight,
  AlignJustify, AlignLeft,
} from "lucide-react";

export interface ColumnDef<T> {
  key: keyof T | string;
  header: string;
  cell?: (row: T) => React.ReactNode;
  sortable?: boolean;
  align?: "left" | "center" | "right";
  width?: string;
  className?: string;
}

interface DataTableProps<T extends Record<string, unknown>> {
  data: T[];
  columns: ColumnDef<T>[];
  searchable?: boolean;
  searchPlaceholder?: string;
  exportable?: boolean;
  exportFilename?: string;
  pageSize?: number;
  className?: string;
  emptyMessage?: string;
  toolbar?: React.ReactNode;
}

type SortDir = "asc" | "desc" | null;

function getValueByKey<T>(obj: T, key: string): unknown {
  return (obj as Record<string, unknown>)[key];
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  searchable = true,
  searchPlaceholder = "Search…",
  exportable = true,
  exportFilename = "export",
  pageSize: defaultPageSize = 25,
  className = "",
  emptyMessage = "No data available",
  toolbar,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [density, setDensity] = useState<"compact" | "default" | "comfortable">("default");
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const paddingMap = { compact: "px-4 py-1.5", default: "px-4 py-3", comfortable: "px-4 py-4" };

  const filtered = useMemo(() => {
    if (!search.trim()) return data;
    const q = search.toLowerCase();
    return data.filter((row) =>
      columns.some((col) => {
        const val = getValueByKey(row, col.key as string);
        return String(val ?? "").toLowerCase().includes(q);
      })
    );
  }, [data, search, columns]);

  const sorted = useMemo(() => {
    if (!sortKey || !sortDir) return filtered;
    return [...filtered].sort((a, b) => {
      const av = getValueByKey(a, sortKey);
      const bv = getValueByKey(b, sortKey);
      const cmp = String(av ?? "") < String(bv ?? "") ? -1 : String(av ?? "") > String(bv ?? "") ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paginated = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = useCallback((key: string) => {
    if (sortKey !== key) { setSortKey(key); setSortDir("asc"); }
    else if (sortDir === "asc") setSortDir("desc");
    else { setSortKey(null); setSortDir(null); }
  }, [sortKey, sortDir]);

  const handleSelectAll = () => {
    if (selected.size === paginated.length) setSelected(new Set());
    else setSelected(new Set(paginated.map((_, i) => page * pageSize + i)));
  };

  const handleSelectRow = (idx: number) => {
    const newSel = new Set(selected);
    if (newSel.has(idx)) newSel.delete(idx); else newSel.add(idx);
    setSelected(newSel);
  };

  const exportCsv = () => {
    const headers = columns.map((c) => c.header).join(",");
    const rows = sorted.map((row) =>
      columns.map((c) => {
        const val = getValueByKey(row, c.key as string);
        const str = String(val ?? "");
        return str.includes(",") ? `"${str}"` : str;
      }).join(",")
    );
    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${exportFilename}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const SortIcon = ({ colKey }: { colKey: string }) => {
    if (sortKey !== colKey) return <ChevronsUpDown className="h-3 w-3 opacity-40" />;
    if (sortDir === "asc") return <ChevronUp className="h-3 w-3 text-primary" />;
    return <ChevronDown className="h-3 w-3 text-primary" />;
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        {searchable && (
          <div className="relative min-w-52 flex-1">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder={searchPlaceholder}
              className="h-9 w-full rounded-md border border-white/5 bg-white/5 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        )}
        {toolbar}
        <div className="ml-auto flex items-center gap-2">
          {/* Density toggle */}
          <div className="flex items-center gap-1 rounded-md border border-white/5 bg-white/5 p-0.5">
            {(["compact", "default", "comfortable"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDensity(d)}
                title={d}
                className={`rounded px-2 py-1 transition-colors ${density === d ? "bg-white/10 text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                {d === "compact" ? <AlignLeft className="h-3.5 w-3.5" /> : d === "comfortable" ? <AlignJustify className="h-3.5 w-3.5" /> : <AlignJustify className="h-3.5 w-3.5" />}
              </button>
            ))}
          </div>
          {exportable && (
            <button
              onClick={exportCsv}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/5 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Selection info */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs">
          <span className="font-medium text-primary">{selected.size} row{selected.size !== 1 ? "s" : ""} selected</span>
          <button onClick={() => setSelected(new Set())} className="text-muted-foreground hover:text-foreground">
            Clear selection
          </button>
        </div>
      )}

      {/* Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10 border-b border-white/5 bg-[oklch(0.15_0.025_260)] text-[10px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.size === paginated.length && paginated.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-white/10 bg-white/5 accent-primary"
                  />
                </th>
                {columns.map((col) => (
                  <th
                    key={col.key as string}
                    className={`py-3 font-semibold ${col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"} ${col.sortable !== false ? "cursor-pointer select-none hover:text-foreground" : ""} ${col.width ? `w-[${col.width}]` : ""}`}
                    style={col.width ? { width: col.width } : undefined}
                    onClick={() => col.sortable !== false && handleSort(col.key as string)}
                  >
                    <div className={`inline-flex items-center gap-1 px-4 ${col.align === "right" ? "flex-row-reverse" : ""}`}>
                      {col.header}
                      {col.sortable !== false && <SortIcon colKey={col.key as string} />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={columns.length + 1} className="py-16 text-center text-sm text-muted-foreground">
                    {search ? `No results for "${search}"` : emptyMessage}
                  </td>
                </tr>
              ) : (
                paginated.map((row, i) => {
                  const globalIdx = page * pageSize + i;
                  const isSelected = selected.has(globalIdx);
                  return (
                    <tr
                      key={globalIdx}
                      className={`group transition-colors ${isSelected ? "bg-primary/5" : "hover:bg-white/[0.025]"}`}
                    >
                      <td className="px-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleSelectRow(globalIdx)}
                          className="rounded border-white/10 bg-white/5 accent-primary"
                        />
                      </td>
                      {columns.map((col) => (
                        <td
                          key={col.key as string}
                          className={`${paddingMap[density]} ${col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : ""} ${col.className ?? ""}`}
                        >
                          {col.cell
                            ? col.cell(row)
                            : String(getValueByKey(row, col.key as string) ?? "—")}
                        </td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-white/5 px-4 py-3">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>
              {sorted.length === 0 ? "0 rows" : `${page * pageSize + 1}–${Math.min((page + 1) * pageSize, sorted.length)} of ${sorted.length}`}
            </span>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}
              className="rounded border border-white/5 bg-white/5 px-2 py-1 text-xs text-foreground focus:outline-none"
            >
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>{n} per page</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1">
            {[
              { icon: ChevronsLeft,  action: () => setPage(0),              disabled: page === 0 },
              { icon: ChevronLeft,   action: () => setPage((p) => p - 1),   disabled: page === 0 },
              { icon: ChevronRight,  action: () => setPage((p) => p + 1),   disabled: page >= totalPages - 1 },
              { icon: ChevronsRight, action: () => setPage(totalPages - 1), disabled: page >= totalPages - 1 },
            ].map(({ icon: Icon, action, disabled }, i) => (
              <button
                key={i}
                onClick={action}
                disabled={disabled}
                className="grid h-7 w-7 place-items-center rounded border border-white/5 bg-white/5 text-muted-foreground transition-colors hover:border-white/10 hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
              >
                <Icon className="h-3.5 w-3.5" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
