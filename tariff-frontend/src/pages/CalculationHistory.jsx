import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Loader2, Search, RefreshCw, Download, Eye, X, Trash2, Pencil } from "lucide-react";
import Papa from "papaparse";
import { toast } from "sonner";
import { Relogin } from "@/components/Relogin";

import { getTransactionHistory, deleteTransactionByID, bulkDeleteTransactions, editTransactions } from "@/api/axiosClient";

export default function CalculationHistory() {
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [showRelogin, setShowRelogin] = useState(false);
  const [q, setQ] = useState("");
  const [viewRow, setViewRow] = useState(null);

  // deletion + selection
  const [deletingId, setDeletingId] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);

  // edit modal
  const [editRow, setEditRow] = useState(null);
  const [editSnap, setEditSnap] = useState({});
  const [savingEdit, setSavingEdit] = useState(false);

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
          // REAL DB id (needed for delete / edit)
          transactionId: r.transactionId ?? r.transactionid ?? snap?.transactionId ?? null,

          // existing fields
          id: idx,
          tariffId: r.tariffId ?? null,
          total: r.total ?? null,
          createdAt: r.created_at ?? r.createdAt ?? null,
          description: r.description ?? "",
          snapshot: snap,
        };
      });

      setItems(mapped);
      setSelectedIds([]);
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

  // single delete
  const handleDelete = async (row) => {
    const id = row?.transactionId;
    if (!id) { toast.error("Invalid record id"); return; }
    if (!window.confirm("Delete this calculation? This cannot be undone.")) return;
    try {
      setDeletingId(id);
      await deleteTransactionByID(id);
      setItems((prev) => prev.filter((r) => r.transactionId !== id));
      setSelectedIds((prev) => prev.filter((x) => x !== id));
      toast.success("Deleted");
    } catch (e) {
      if (e?.response?.status === 401) { setShowRelogin(true); return; }
      if (e?.response?.status === 404) toast.error("Not found or not yours");
      else toast.error("Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  // select + bulk delete
  const toggleSelect = (row) => {
    const id = row?.transactionId;
    if (!id) return;
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!window.confirm(`Delete ${selectedIds.length} selected item(s)? This cannot be undone.`)) return;
    try {
      await bulkDeleteTransactions(selectedIds); // calls DELETE /transactionHistory?ids=...
      setItems((prev) => prev.filter((r) => !selectedIds.includes(r.transactionId)));
      setSelectedIds([]);
      toast.success("Deleted selected");
    } catch (e) {
      if (e?.response?.status === 401) { setShowRelogin(true); return; }
      toast.error("Bulk delete failed");
    }
  };

  // ---------- Edit flow ----------
  const openEdit = (row) => {
    const base = {
      total: row?.snapshot?.total ?? "",
      category: row?.snapshot?.category ?? "",
      quantity: row?.snapshot?.quantity ?? "",
      tariffId: row?.snapshot?.tariffId ?? "",
      unitname: row?.snapshot?.unitname ?? "",
      adValorem: row?.snapshot?.adValorem ?? row?.snapshot?.advalorem ?? "",
      customsValue: row?.snapshot?.customsValue ?? "",
      partnerCountry: row?.snapshot?.partnerCountry ?? "",
      reporterCountry: row?.snapshot?.reporterCountry ?? "",
      specificPerUnit: row?.snapshot?.specificPerUnit ?? row?.snapshot?.specificperunit ?? "",
      descriptionwcountry: row?.snapshot?.descriptionwcountry ?? "",
    };
    setEditRow(row);
    setEditSnap(base);
  };

  const updateField = (k, v) => setEditSnap((s) => ({ ...s, [k]: v }));

  // convert numerics before sending; leave others as-is
  const prepareBody = (snap) => ({
    ...snap,
    total: toNum(snap.total),
    quantity: toNum(snap.quantity),
    tariffId: toNum(snap.tariffId),
    adValorem: toNum(snap.adValorem),
    customsValue: toNum(snap.customsValue),
    specificPerUnit: toNum(snap.specificPerUnit),
  });

  // local minimal PUT (self-contained)
  const putSnapshot = async (transactionId, snapshot) => {
    const { data } = await editTransactions(transactionId, snapshot);
    return data;
  };

  const onSaveEdit = async () => {
    if (!editRow?.transactionId) return;
    setSavingEdit(true);
    const id = editRow.transactionId;
    const body = prepareBody(editSnap);
    try {
      const res = await putSnapshot(id, body);
      const newSnap = res?.snapshot ?? body;

      // optimistic list update
      setItems((prev) =>
        prev.map((r) =>
          r.transactionId === id ? { ...r, snapshot: newSnap } : r
        )
      );

      // if details modal is open for same row, reflect changes
      setViewRow((prev) => (prev && prev.transactionId === id ? { ...prev, snapshot: newSnap } : prev));

      toast.success("Snapshot updated");
      setEditRow(null);
    } catch (e) {
      toast.error(e?.message ?? "Update failed");
    } finally {
      setSavingEdit(false);
    }
  };

  const Row = ({ row }) => {
    const rate = fmtRate(row.snapshot);
    const category = row.snapshot?.category ?? "—";
    const titleId = getTariffId(row);
    const rid = row.transactionId;

    return (
      <div className="p-3 rounded-lg border bg-card">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              className="h-4 w-4"
              checked={selectedIds.includes(rid)}
              onChange={() => toggleSelect(row)}
              disabled={!rid}
              aria-label="Select row"
            />
            <Badge variant="secondary" className="font-mono">#{titleId ?? "—"}</Badge>
            <span className="text-xs text-muted-foreground">
              {row.createdAt ? new Date(row.createdAt).toLocaleString() : "—"}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Button size="sm" variant="ghost" onClick={() => setViewRow(row)} aria-label="View">
              <Eye className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={() => openEdit(row)} aria-label="Edit">
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleDelete(row)}
              disabled={deletingId === rid || !rid}
              aria-label="Delete"
            >
              <Trash2 className={`h-4 w-4 ${deletingId === rid ? "animate-pulse" : ""}`} />
            </Button>
          </div>
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
            <div className="flex flex-col gap-2 p-4 bg-muted/30 rounded-xl border mb-3">
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

            {selectedIds.length > 0 && (
              <div className="px-0 mb-4">
                <div className="flex items-center gap-2">
                  <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
                    Delete selected ({selectedIds.length})
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedIds([])}>
                    Clear selection
                  </Button>
                </div>
              </div>
            )}
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
              {filtered.map((row) => (
                <Row key={row.transactionId ?? row.id} row={row} />
              ))}
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
            {viewRow?.transactionId && (
              <Button variant="destructive" onClick={() => { handleDelete(viewRow); setViewRow(null); }}>
                Delete
              </Button>
            )}
            <Button onClick={() => setViewRow(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* edit modal */}
      <Dialog open={!!editRow} onOpenChange={() => setEditRow(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Snapshot (Transaction #{editRow?.transactionId})</DialogTitle>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4 py-2">
            <div className="col-span-1">
              <Label>Total</Label>
              <Input value={editSnap.total ?? ""} onChange={(e) => updateField("total", e.target.value)} />
            </div>
            <div className="col-span-1">
              <Label>Category</Label>
              <Input value={editSnap.category ?? ""} onChange={(e) => updateField("category", e.target.value)} />
            </div>

            <div className="col-span-1">
              <Label>Quantity</Label>
              <Input value={editSnap.quantity ?? ""} onChange={(e) => updateField("quantity", e.target.value)} />
            </div>
            <div className="col-span-1">
              <Label>Tariff ID</Label>
              <Input value={editSnap.tariffId ?? ""} onChange={(e) => updateField("tariffId", e.target.value)} />
            </div>

            <div className="col-span-1">
              <Label>Unit Name</Label>
              <Input value={editSnap.unitname ?? ""} onChange={(e) => updateField("unitname", e.target.value)} />
            </div>
            <div className="col-span-1">
              <Label>Ad Valorem</Label>
              <Input value={editSnap.adValorem ?? ""} onChange={(e) => updateField("adValorem", e.target.value)} />
            </div>

            <div className="col-span-1">
              <Label>Customs Value</Label>
              <Input value={editSnap.customsValue ?? ""} onChange={(e) => updateField("customsValue", e.target.value)} />
            </div>
            <div className="col-span-1">
              <Label>Specific / Unit</Label>
              <Input value={editSnap.specificPerUnit ?? ""} onChange={(e) => updateField("specificPerUnit", e.target.value)} />
            </div>

            <div className="col-span-1">
              <Label>Partner Country</Label>
              <Input value={editSnap.partnerCountry ?? ""} onChange={(e) => updateField("partnerCountry", e.target.value)} />
            </div>
            <div className="col-span-1">
              <Label>Reporter Country</Label>
              <Input value={editSnap.reporterCountry ?? ""} onChange={(e) => updateField("reporterCountry", e.target.value)} />
            </div>

            <div className="col-span-2">
              <Label>Description (with country)</Label>
              <Input
                value={editSnap.descriptionwcountry ?? ""}
                onChange={(e) => updateField("descriptionwcountry", e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditRow(null)}>Cancel</Button>
            <Button onClick={onSaveEdit} disabled={savingEdit}>
              {savingEdit && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}

/* ---------- helpers ---------- */
async function safeReadText(res) {
  try { return await res.text(); } catch { return ""; }
}

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
    const specificPart = (qty ?? 0) * (spec ?? 0);
    const multiplier = 1 + (adval ?? 0);
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
  const t = s?.total ?? s?.result?.total ?? row?.total;
  return t == null ? null : Number(t);
}
