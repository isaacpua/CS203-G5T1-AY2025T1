import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Loader2, Search, RefreshCw, Download, Eye, X } from "lucide-react";
import Papa from "papaparse";
import { toast } from "sonner";
import { Relogin } from "@/components/Relogin";

import { getTransactionHistory } from "@/api/axiosClient";

export default function CalculationHistory() {
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [showRelogin, setShowRelogin] = useState(false);
  const [q, setQ] = useState("");
  const [viewRow, setViewRow] = useState(null);

  const load = async (asRefresh = false) => {
    setError("");
    asRefresh ? setIsRefreshing(true) : setLoading(true);
    try {
      const { data } = await getTransactionHistory();
      const arr = Array.isArray(data) ? data : [];

      const mapped = arr.map((r, idx) => {
        const raw = r.snapshot ?? r.snapshotJson; // object or string
        let snap = raw;
        if (typeof raw === "string") {
          try { snap = JSON.parse(raw); } catch { snap = null; }
        }
        return {
          id: idx,
          tariffId: r.tariffId ?? null,                // table value (fallback only)
          total: r.total ?? null,
          createdAt: r.created_at ?? r.createdAt ?? null,
          description: r.description ?? "",            // table value (fallback only)
          snapshot: snap,                              // preferred source
        };
      });

      setItems(mapped);
      if (asRefresh) toast.success(`Loaded ${mapped.length} records`);
    } catch (e) {
      if (e?.response?.status === 401) { setShowRelogin(true); return; }
      console.error(e);
      setError("Failed to fetch calculation history.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => { load(false); }, []);
  const filtered = filterItems(items, q);

  const exportCSV = async () => {
    try {
      setIsExporting(true);
      const rows = filtered.map((r) => ({
        "Time": r.createdAt ? new Date(r.createdAt).toISOString() : "",
        "Tariff ID": getTariffId(r) ?? "",
        "Description": getDescription(r),
        "Category": r.snapshot?.category ?? "",
        "Rate (pretty)": fmtRate(r.snapshot),
        "Total Duty": getTotal(r) != null ? String(getTotal(r)) : "",
      }));
      const csv = Papa.unparse(rows, { header: true, skipEmptyLines: true });
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `calculation_history_${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success(`Exported ${rows.length} records`);
    } catch (e) {
      if (e?.response?.status === 401) { setShowRelogin(true); return; }
      console.error(e);
      toast.error("Export failed.");
    } finally {
      setIsExporting(false);
    }
  };

  const Row = ({ row }) => {
    const rate = fmtRate(row.snapshot);
    const category = row.snapshot?.category ?? "—";
    const titleId = getTariffId(row);
    return (
      <div className="p-3 rounded-lg border bg-card">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="font-mono">#{titleId ?? "—"}</Badge>
            <span className="text-xs text-muted-foreground">
              {row.createdAt ? new Date(row.createdAt).toLocaleString() : "—"}
            </span>
          </div>
          <Button size="sm" variant="ghost" onClick={() => setViewRow(row)}>
            <Eye className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-2 text-sm">{getDescription(row)}</div>

        <div className="mt-1 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Rate:</span>{" "}
          {rate}
          {category !== "—" && <span className="ml-2">• <span className="uppercase">{category}</span></span>}
        </div>

        <div className="mt-2 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Total:</span>{" "}
          {getTotal(row) != null ? `$${to2(getTotal(row))}` : "—"}
        </div>
      </div>
    );
  };

  const snap = viewRow?.snapshot ?? null;
  const ratePretty = fmtRate(snap);

  return (
    <TooltipProvider>
      {showRelogin && <Relogin />}

      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-4 md:p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <CardTitle className="text-xl md:text-2xl font-bold text-foreground">Calculation History</CardTitle>
              <CardDescription className="text-sm md:text-base text-muted-foreground">
                View your saved tariff calculations
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" onClick={() => load(true)} disabled={isRefreshing}>
                    <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Refresh</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" onClick={exportCSV} disabled={isExporting || filtered.length === 0}>
                    <Download className={`h-4 w-4 ${isExporting ? "animate-spin" : ""}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export CSV</TooltipContent>
              </Tooltip>
            </div>
          </div>
        </CardHeader>

        <CardContent className="px-0 pt-4 md:pt-6 pb-6 md:pb-8">
          <div className="px-4 md:px-6">
            <div className="flex flex-col gap-2 p-4 bg-muted/30 rounded-xl border mb-6">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-10 pr-8"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Description, tariff ID…"
                />
                {q && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                    onClick={() => setQ("")}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {error ? (
            <div className="flex flex-col items-center justify-center p-12 h-[520px] bg-destructive/10 border border-destructive/20 rounded-xl">
              <div className="text-center">
                <div className="w-16 h-16 bg-destructive/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="h-8 w-8 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Error Loading</h3>
                <p className="text-muted-foreground mb-4">{error}</p>
                <Button onClick={() => load(false)} variant="outline">
                  <RefreshCw className="mr-2 h-4 w-4" />Try Again
                </Button>
              </div>
            </div>
          ) : loading ? (
            <div className="border rounded-xl bg-card h-[520px] grid place-items-center">
              <div className="flex items-center space-x-3">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="text-muted-foreground">Loading history…</span>
              </div>
            </div>
          ) : filtered.length > 0 ? (
            <div className="px-4 md:px-6 space-y-3">
              {filtered.map((row) => <Row key={row.id} row={row} />)}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-12 h-[520px] bg-muted/30 border rounded-xl mx-4 md:mx-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No History</h3>
                <p className="text-muted-foreground mb-4">No saved calculations found.</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* details modal */}
      <Dialog open={!!viewRow} onOpenChange={() => setViewRow(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Badge variant="secondary" className="font-mono">#{getTariffId(viewRow) ?? "—"}</Badge>
              <span>Calculation Details</span>
            </DialogTitle>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4 py-4 text-sm">
            <div>
              <span className="text-muted-foreground">Time:</span>{" "}
              {viewRow?.createdAt ? new Date(viewRow.createdAt).toLocaleString() : "—"}
            </div>
            <div>
              <span className="text-muted-foreground">Tariff ID:</span>{" "}
              {getTariffId(viewRow) ?? "—"}
            </div>

            <div className="col-span-2">
              <span className="text-muted-foreground">Description:</span>
              <div className="mt-1 bg-muted/40 rounded p-2">
                {getDescription(viewRow)}
              </div>
            </div>

            {/* Rate */}
            <div className="col-span-2">
              <div className="font-medium mb-1">Rate</div>
              <div className="rounded-lg border bg-muted/30 p-3 space-y-1">
                <div><span className="text-muted-foreground">Category:</span> {snap?.category ?? "—"}</div>
                <div><span className="text-muted-foreground">Details:</span> {ratePretty}</div>
              </div>
            </div>

            {/* Workings */}
            <div className="col-span-2">
              <div className="font-medium mb-1">Workings</div>
              <pre className="rounded-lg border bg-black/20 p-3 text-xs leading-5 overflow-auto whitespace-pre-wrap">
                {snap ? renderWorkingsFromSnap(snap) : "—"}
              </pre>
            </div>

            <div className="col-span-2">
              <span className="text-muted-foreground">Total Duty:</span>{" "}
              {getTotal(viewRow) != null ? `$${to2(getTotal(viewRow))}` : "—"}
            </div>
          </div>

          <DialogFooter>
            <Button onClick={() => setViewRow(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}

/* ---------- helpers ---------- */
function to2(n) {
  const x = Number(n);
  return Number.isFinite(x) ? x.toFixed(2) : n;
}

function fmtRate(rowOrSnap) {
  if (!rowOrSnap) return "—";
  const adv = toNum(rowOrSnap.adValorem ?? rowOrSnap.advalorem);
  const spec = toNum(rowOrSnap.specificPerUnit ?? rowOrSnap.specificperunit);
  const parts = [];
  if (adv != null) parts.push(`${(adv * 100).toFixed(2).replace(/\.00$/, "")}% ad valorem`);
  if (spec != null) parts.push(`$${to2(spec)} per Unit`);
  return parts.length ? parts.join(" + ") : "—";
}

function toNum(x) {
  if (x == null || x === "") return null;
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

/** ALWAYS prefer snapshot values (time-of-creation); fall back to table if missing */
function getTariffId(row) {
  return row?.snapshot?.tariffId ?? row?.tariffId ?? null;
}
function getDescription(row) {
  return row?.snapshot?.descriptionwcountry ?? row?.description ?? "—";
}

/* text search uses snapshot-backed getters */
function filterItems(items, q) {
  const t = q.trim().toLowerCase();
  if (!t) return items;
  return items.filter((r) => {
    const fields = [
      getDescription(r),
      getTariffId(r) != null ? String(getTariffId(r)) : "",
      r.snapshot?.category ?? r.category ?? "",
    ];
    return fields.some((f) => f.toLowerCase().includes(t));
  });
}

function renderWorkingsFromSnap(snap) {
  if (!snap) return "—";
  const cat = (snap.category || "").toUpperCase();

  const adval = toNum(snap.adValorem ?? snap.advalorem);
  const spec = toNum(snap.specificPerUnit ?? snap.specificperunit);
  const qty = toNum(snap.quantity ?? snap.inputs?.quantity);
  const val = toNum(snap.customsValue ?? snap.inputs?.customsValue);
  const total = toNum(snap.total ?? snap.result?.total);
  const unit = snap.unitname ?? snap.unitName ?? "unit";

  const fmt = (x) => Number.isFinite(x) ? x.toFixed(2) : "—";
  const fmtPct = (x) => Number.isFinite(x) ? `${(x * 100).toFixed(2).replace(/\.00$/, "")}%` : "—";
  const avMult = adval != null ? 1 + adval : null;

  const lines = [];
  lines.push(`Category: ${cat}`);

  if (cat === "AD_VALOREM" && adval != null && val != null) {
    lines.push(`Ad Valorem Rate: ${fmtPct(adval)} (multiplier = ${fmt(avMult)})`);
    lines.push(`Total = Declared Value × (1 + rate)`);
    lines.push(`= $${fmt(val)} × ${fmt(avMult)} = $${fmt(total)}`);
  } else if (cat === "SPECIFIC_PER_UNIT" && spec != null && qty != null) {
    lines.push(`Specific Rate: $${fmt(spec)} per ${unit}`);
    lines.push(`Total = Quantity × Rate`);
    lines.push(`= ${fmt(qty)} × $${fmt(spec)} = $${fmt(total)}`);
  } else if (cat === "COMPOSITE" && adval != null && spec != null && qty != null) {
    const specificPart = qty * spec;
    const multiplier = 1 + adval;
    lines.push(`Specific Rate: $${fmt(spec)} per ${unit}`);
    lines.push(`Ad Valorem Rate: ${fmtPct(adval)} (multiplier = ${fmt(multiplier)})`);
    lines.push(`Step 1 — Specific Part = ${fmt(qty)} × $${fmt(spec)} = $${fmt(specificPart)}`);
    lines.push(`Step 2 — Apply Ad Valorem: $${fmt(specificPart)} × ${fmt(multiplier)} = $${fmt(total ?? specificPart * multiplier)}`);
  } else {
    lines.push("— No sufficient data for workings —");
  }

  return lines.join("\n");
}

function getTotal(row) {
  const s = row?.snapshot;
  // support either shape: { total } or { result: { total } }
  const t = s?.total ?? s?.result?.total ?? row?.total;
  return t == null ? null : Number(t);
}
