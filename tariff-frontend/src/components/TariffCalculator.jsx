import { useEffect, useMemo, useState } from "react";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Search, Calculator, Terminal } from "lucide-react";


function TariffSearchAndCalc() {
  // -------- Search state --------
  const [mode, setMode] = useState("id"); // search mode: "id" | "hts8" | "desc"
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0); //current page
  const [size, setSize] = useState(10);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [results, setResults] = useState({ content: [], totalPages: 0, number: 0, size: 10 });

  // -------- Selection + compute state --------
  const [selected, setSelected] = useState(null); // the row clicked from the results
  const [declaredValue, setDeclaredValue] = useState("");
  const [quantity, setQuantity] = useState("");
  const [uom, setUom] = useState("/unit"); //normalised UOM string
  const [computing, setComputing] = useState(false);
  const [computeError, setComputeError] = useState("");
  const [computeRes, setComputeRes] = useState(null);


  const debouncedQuery = useDebounce(query, 300); //because i dont want to call the API on every keystroke

  // ---- search handler ----
  useEffect(() => { //rerun the search whenever the search mode changes
    
    if (mode === "desc" && debouncedQuery.trim() === "") {
      // no empty description searches
      setResults({ content: [], totalPages: 0, number: 0, size });
      return;
    }
    if (mode !== "desc" && query.trim() === "") {
      // no empty id/hts8 searches
      setResults({ content: [], totalPages: 0, number: 0, size });
      return;
    }

    const fetchPage = async () => {
      setSearching(true);
      setSearchError("");
      try {
        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("size", String(size));

        if (mode === "id") params.set("id", query.trim());
        if (mode === "hts8") params.set("hts8", query.trim());
        if (mode === "desc") params.set("q", debouncedQuery.trim());

        const { data } = await axiosClient.get(`/tariffs/search?${params.toString()}`);
        setResults(data);
      } catch (e) {
        setSearchError("Search failed. Check backend /tariffs/search.");
        setResults({ content: [], totalPages: 0, number: 0, size });
        console.error(e);
      } finally {
        setSearching(false);
      }
    };

    fetchPage();
  }, [mode, debouncedQuery, query, page, size]);

  // reset when mode changes like if im switching from ID --> HTS8, it clears the thing
  useEffect(() => {
    setPage(0);
    setResults({ content: [], totalPages: 0, number: 0, size });
    setSelected(null);
    setComputeRes(null);
  }, [mode]);

  // ---- compute handler ----
  const onCompute = async () => {
    if (!selected) return;
    setComputing(true);
    setComputeError("");
    setComputeRes(null);
    try {
      const body = {
        declaredValue: numOrZero(declaredValue),
        quantity: numOrZero(quantity),
        uom, // must match backend normalization (e.g. "/unit", "/kg")
      };
      const { data } = await axiosClient.post(`/tariffs/${selected.id}/compute`, body); //asking the backend to do the computing part
      setComputeRes(data);
    } catch (e) {
      setComputeError("Compute failed. Check /tariffs/{id}/compute.");
      console.error(e);
    } finally {
      setComputing(false);
    }
  };

  // ---- UI ----
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Search className="h-5 w-5" />Search Tariffs</CardTitle>
          <CardDescription>Find by ID, HTS8 code, or brief description.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-1">
              <Label>Search by</Label>
              <Select value={mode} onValueChange={(v) => { setMode(v); setQuery(""); }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="id">ID</SelectItem>
                  <SelectItem value="hts8">HTS8</SelectItem>
                  <SelectItem value="desc">Description</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2">
              <Label>{mode === "id" ? "ID" : mode === "hts8" ? "HTS8 Code" : "Brief Description"}</Label>
              <Input
                placeholder={mode === "desc" ? "e.g., sunglasses, lenses..." : "Enter number"}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                inputMode={mode === "desc" ? "text" : "numeric"}
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Label>Page size</Label>
            <Select value={String(size)} onValueChange={(v) => { setSize(Number(v)); setPage(0); }}>
              <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
              </SelectContent>
            </Select>
            <div className="ml-auto text-sm text-muted-foreground">
              {searching && <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Searching…</span>}
            </div>
          </div>

          {/* Results list */}
          <div className="border rounded-md divide-y">
            {results.content.length === 0 && !searching && (
              <div className="p-4 text-sm text-muted-foreground">No results.</div>
            )}
            {results.content.map((row) => (
              <button
                key={row.id}
                className={`w-full text-left p-3 hover:bg-muted/50 ${selected?.id === row.id ? "bg-muted/70" : ""}`}
                onClick={() => { setSelected(row); setComputeRes(null); }}
              >
                <div className="flex justify-between">
                  <div className="font-medium">HTS8: {row.hts8} · ID: {row.id}</div>
                  <div className="text-xs">{row.overallKind}{row.isFree ? " · FREE" : ""}</div>
                </div>
                <div className="text-sm text-muted-foreground">{row.briefDescription}</div>
                <div className="text-xs font-mono mt-1">rate: {row.mfnTextRate}</div>
              </button>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center">
            <Button variant="outline" disabled={page <= 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
              Prev
            </Button>
            <div className="text-sm">Page {results.number + 1} / {Math.max(results.totalPages, 1)}</div>
            <Button
              variant="outline"
              disabled={results.number + 1 >= results.totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>

          {searchError && (
            <Alert variant="destructive">
              <AlertTitle>Search Error</AlertTitle>
              <AlertDescription>{searchError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Compute Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Calculator className="h-5 w-5" />Compute Duty</CardTitle>
          <CardDescription>
            Select a row on the left, then enter declared value, quantity, and unit.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!selected ? (
            <div className="text-sm text-muted-foreground">Select a tariff from search results.</div>
          ) : (
            <>
              <div className="text-sm">
                <div className="font-medium">HTS8: {selected.hts8} · ID: {selected.id}</div>
                <div className="text-muted-foreground">{selected.briefDescription}</div>
                <div className="font-mono text-xs mt-1">rate: {selected.mfnTextRate}</div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-1">
                  <Label>Declared Value ($)</Label>
                  <Input value={declaredValue} onChange={(e) => setDeclaredValue(e.target.value)} placeholder="e.g. 1000" />
                </div>
                <div className="col-span-1">
                  <Label>Quantity</Label>
                  <Input value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="e.g. 200" />
                </div>
                <div className="col-span-1">
                  <Label>Unit of Measure</Label>
                  <Select value={uom} onValueChange={setUom}>
                    <SelectTrigger><SelectValue placeholder="Select UOM" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="/unit">/unit (each, piece)</SelectItem>
                      <SelectItem value="/kg">/kg</SelectItem>
                      <SelectItem value="/liter">/liter</SelectItem>
                      <SelectItem value="/doz">/doz</SelectItem>
                      <SelectItem value="/gross">/gross</SelectItem>
                      <SelectItem value="/m3">/m3</SelectItem>
                      <SelectItem value="/m2">/m2</SelectItem>
                      <SelectItem value="/m">/m</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button className="w-full" onClick={onCompute} disabled={computing}>
                {computing ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Computing…</> : "Compute Duty"}
              </Button>

              {computeRes && (
                <Alert className="mt-2">
                  <Terminal className="h-4 w-4" />
                  <AlertTitle>Duty</AlertTitle>
                  <AlertDescription className="font-mono">
                    <div>Total Duty: ${Number(computeRes.totalDuty).toFixed(2)}</div>
                    {Array.isArray(computeRes.breakdown) && computeRes.breakdown.length > 0 && (
                      <div className="mt-1">
                        {computeRes.breakdown.map((c, i) => (
                          <div key={i}>
                            • {c.kind}: duty={fmtMoney(c.dutyAmount)} | adVal={c.adValorem ?? 0} | spec={c.specificPerUnit ?? 0} {c.unit ?? ""} {c.qualifier ?? ""}
                          </div>
                        ))}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}

              {computeError && (
                <Alert variant="destructive" className="mt-2">
                  <AlertTitle>Compute Error</AlertTitle>
                  <AlertDescription>{computeError}</AlertDescription>
                </Alert>
              )}
            </>
          )}
        </CardContent>
        <CardFooter />
      </Card>
    </div>
  );
}

export default TariffSearchAndCalc;

/* ------------ helpers ------------ */
function useDebounce(value, delayMs = 300) { //wait before updating
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return v;
}
function numOrZero(x) { //parses the number properly
  const n = Number(x);
  return Number.isFinite(n) ? n : 0;
}
function fmtMoney(x) { //formates the money
  const n = Number(x);
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : "$0.00";
}
