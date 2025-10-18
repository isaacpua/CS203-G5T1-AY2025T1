// src/pages/CalculationHistory.jsx
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

// API: returns List<TransactionLineDTO>
import { getTransactionHistory } from "@/api/axiosClient";

export default function CalculationHistory() {
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);              // ← simple list from backend
  const [showRelogin, setShowRelogin] = useState(false);

  const [q, setQ] = useState("");                      // local search
  const [viewRow, setViewRow] = useState(null);

  const load = async (asRefresh = false) => {
    setError("");
    asRefresh ? setIsRefreshing(true) : setLoading(true);
    try {
      const { data } = await getTransactionHistory();
      const arr = Array.isArray(data) ? data : [];

      // normalize keys to what UI will use
      const mapped = arr.map((r, idx) => ({
        id: idx,                                      // no ID in DTO, use index
        tariffId: r.tariffId ?? null,
        total: r.total ?? null,
        createdAt: r.created_at ?? r.createdAt ?? null, // handle snake or camel just in case
        description: r.description ?? "",
      }));

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
        "Tariff ID": r.tariffId ?? "",
        "Description": r.description ?? "",
        "Total Duty": r.total != null ? String(r.total) : "",
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

  const Row = ({ row }) => (
    <div className="p-3 rounded-lg border bg-card">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="font-mono">#{row.tariffId ?? "—"}</Badge>
          <span className="text-xs text-muted-foreground">
            {row.createdAt ? new Date(row.createdAt).toLocaleString() : "—"}
          </span>
        </div>
        <Button size="sm" variant="ghost" onClick={() => setViewRow(row)}>
          <Eye className="h-4 w-4" />
        </Button>
      </div>
      <div className="mt-2 text-sm">{row.description || "—"}</div>
      <div className="mt-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">Total:</span>{" "}
        {row.total != null ? `$${Number(row.total).toFixed(2)}` : "—"}
      </div>
    </div>
  );

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
            {/* simple client-side search */}
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

          {/* body */}
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
              <Badge variant="secondary" className="font-mono">#{viewRow?.tariffId ?? "—"}</Badge>
              <span>Calculation Details</span>
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4 text-sm">
            <div><span className="text-muted-foreground">Time:</span> {viewRow?.createdAt ? new Date(viewRow.createdAt).toLocaleString() : "—"}</div>
            <div><span className="text-muted-foreground">Tariff ID:</span> {viewRow?.tariffId ?? "—"}</div>
            <div className="col-span-2">
              <span className="text-muted-foreground">Description:</span>
              <div className="mt-1 bg-muted/40 rounded p-2">{viewRow?.description || "—"}</div>
            </div>
            <div className="col-span-2"><span className="text-muted-foreground">Total Duty:</span> {viewRow?.total != null ? `$${Number(viewRow.total).toFixed(2)}` : "—"}</div>
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
function filterItems(items, q) {
  const t = q.trim().toLowerCase();
  if (!t) return items;
  return items.filter((r) => {
    const fields = [
      r.description ?? "",
      r.tariffId != null ? String(r.tariffId) : "",
    ];
    return fields.some((f) => f.toLowerCase().includes(t));
  });
}
