import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Loader2, Search, Calculator, Terminal } from "lucide-react";

function TariffSearchAndCalc() {
  // -------- Search state --------
  const [mode, setMode] = useState("id"); // "id" | "hts8" | "desc"
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [results, setResults] = useState({
    content: [],
    totalPages: 0,
    number: 0,
    size: 10,
  });

  // -------- Selection + compute state --------
  const [selected, setSelected] = useState(null);

  // legacy single-value inputs
  const [declaredValue, setDeclaredValue] = useState("");
  const [quantity, setQuantity] = useState("");
  const [uom, setUom] = useState("/unit");

  // qualifier-specific declared values (RAW qualifier keys)
  const [qualifierValues, setQualifierValues] = useState({});

  // per-specific-unit quantities, UI-only (keys like "each", "/jewel", "/1000")
  const [specificQty, setSpecificQty] = useState({});

  const [computing, setComputing] = useState(false);
  const [computeError, setComputeError] = useState("");
  const [computeRes, setComputeRes] = useState(null);

  const debouncedQuery = useDebounce(query, 300);

  // ---- search handler ----
  useEffect(() => {
    if (mode === "desc" && debouncedQuery.trim() === "") {
      setResults({ content: [], totalPages: 0, number: 0, size });
      return;
    }
    if (mode !== "desc" && query.trim() === "") {
      setResults({ content: [], totalPages: 0, number: 0, size });
      return;
    }
    if ((mode === "id" || mode === "hts8") && !isIntegerLike(query)) {
      setSearchError("Please input an integer.");
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

  // reset paging + compute when mode changes
  useEffect(() => {
    setPage(0);
    setResults({ content: [], totalPages: 0, number: 0, size });
    setSelected(null);
    setComputeRes(null);
  }, [mode]);

  // Reset all inputs/results when a new tariff is selected, then initialize empty fields
  useEffect(() => {
    // hard reset
    setDeclaredValue("");
    setQuantity("");
    setComputeRes(null);
    setComputeError("");
    setQualifierValues({});
    setSpecificQty({});

    if (!selected?.mfnTextRate) return;

    const { percentQuals, specificUnits } = parseParts(selected.mfnTextRate);

    // initialize fresh, empty fields
    setQualifierValues(Object.fromEntries(percentQuals.map((q) => [q, ""])));
    setSpecificQty(Object.fromEntries(specificUnits.map((u) => [u, ""])));

    // snap uom when there's exactly one specific unit
    if (specificUnits.length === 1) setUom(specificUnits[0]);
    else setUom("");
  }, [selected?.id]);

  // ---- compute handler ----
  const onCompute = async () => {
    if (!selected) return;
    setComputing(true);
    setComputeError("");
    setComputeRes(null);
    try {
      const {
        hasSpecific,
        hasPercent,
        percentQuals,
        hasUnqualifiedPercent,
        specificUnits,
      } = parseParts(selected.mfnTextRate || "");

      const cascading = hasUnqualifiedPercent && specificUnits.length > 0;
      const pureSpecific = hasSpecific && !hasPercent;
      const multiSpecific = specificUnits.length > 1;

      // qualifier % values (RAW keys)
      const needsQualifierDVs = hasPercent && percentQuals.length > 0;
      const declaredByQualifier = needsQualifierDVs
        ? Object.fromEntries(
            percentQuals
              .map((rawQ) => [rawQ, toDecimalOrNull(qualifierValues[rawQ])])
              .filter(([, v]) => v !== null)
          )
        : undefined;

      // ----- Legacy quantity/uom to send to backend -----
      let qtyForLegacy = toDecimalOrZero(quantity);
      let uomForLegacy = uom;

      if (pureSpecific) {
        if (specificUnits.length === 1) {
          // Single-unit pure specific
          const unit = specificUnits[0];
          qtyForLegacy = toDecimalOrZero(specificQty[unit] || quantity);
          // map UI unit to backend unit (e.g., /gross -> /line for /line/ gross patterns)
          uomForLegacy = uiUnitToBackendUnit(selected.mfnTextRate, unit);
        } else {
          // Multi-specific fallback
          qtyForLegacy = toDecimalOrZero(quantity);
          uomForLegacy = "";
        }
      } else if (hasSpecific) {
        if (specificUnits.length === 1) {
          // prefer the per-unit field if user typed there; else normal Quantity
          const unit = specificUnits[0];
          const perUnit = toDecimalOrNull(specificQty[unit]);
          qtyForLegacy = perUnit != null ? perUnit : toDecimalOrZero(quantity);
          // map UI unit to backend unit
          uomForLegacy = uiUnitToBackendUnit(selected.mfnTextRate, unit);
        } else {
          // multi-specific: use ONE qty (first non-empty per-unit else normal Quantity)
          const perUnitVals = specificUnits
            .map((u) => toDecimalOrNull(specificQty[u]))
            .filter((v) => v !== null);
          qtyForLegacy = perUnitVals[0] ?? toDecimalOrZero(quantity);

          // IMPORTANT: blank uom → backend fallback applies the same qty to ALL specifics
          if (cascading && multiSpecific) uomForLegacy = "";
        }
      }

      const body = {
        // send DV only for pure ad valorem (no specifics)
        ...(!hasSpecific && hasUnqualifiedPercent
          ? { declaredValue: toDecimalOrZero(declaredValue) }
          : {}),

        ...(hasSpecific
          ? { quantity: qtyForLegacy, uom: uomForLegacy }
          : { uom: uomForLegacy }),

        ...(declaredByQualifier && Object.keys(declaredByQualifier).length > 0
          ? { declaredByQualifier }
          : {}),
      };

      const { data } = await axiosClient.post(
        `/tariffs/compute?id=${selected.id}`,
        body
      );
      setComputeRes(data);
    } catch (e) {
      setComputeError("Compute failed. Check /tariffs/compute.");
      console.error(e);
    } finally {
      setComputing(false);
    }
  };

  // ---- derived UI flags ----
  const rateText = selected?.mfnTextRate ?? "";
  const {
    hasSpecific,
    hasPercent,
    percentQuals,
    hasUnqualifiedPercent,
    specificUnits,
  } = selected
    ? parseParts(rateText)
    : {
        hasSpecific: false,
        hasPercent: false,
        percentQuals: [],
        hasUnqualifiedPercent: false,
        specificUnits: [],
      };

  const cascading = hasUnqualifiedPercent && specificUnits.length > 0;
  const needsQualifierDVs = hasPercent && percentQuals.length > 0;
  const pureAdValorem =
    hasPercent && !hasSpecific && !needsQualifierDVs && hasUnqualifiedPercent;
  const pureSpecific = hasSpecific && !hasPercent;

  // ---- UI ----
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Tariffs
          </CardTitle>
          <CardDescription>
            Find by ID, HTS8 code, or brief description.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-1">
              <Label>Search by</Label>
              <Select
                value={mode}
                onValueChange={(v) => {
                  setMode(v);
                  setQuery("");
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="id">ID</SelectItem>
                  <SelectItem value="hts8">HTS8</SelectItem>
                  <SelectItem value="desc">Description</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2">
              <Label>
                {mode === "id" ? "ID" : mode === "hts8" ? "HTS8 Code" : "Brief Description"}
              </Label>
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
            <Select
              value={String(size)}
              onValueChange={(v) => {
                setSize(Number(v));
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
              </SelectContent>
            </Select>
            <div className="ml-auto text-sm text-muted-foreground">
              {searching && (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" /> Searching…
                </span>
              )}
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
                className={`w-full text-left p-3 hover:bg-muted/50 ${
                  selected?.id === row.id ? "bg-muted/70" : ""
                }`}
                onClick={() => {
                  // just set; effect will clear & re-init inputs
                  setSelected(row);
                }}
              >
                <div className="flex justify-between">
                  <div className="font-medium">
                    HTS8: {row.hts8} · ID: {row.id}
                  </div>
                  <div className="text-xs">
                    {row.overallKind}
                    {row.isFree ? " · FREE" : ""}
                  </div>
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
            <div className="text-sm">
              Page {results.number + 1} / {Math.max(results.totalPages, 1)}
            </div>
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
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Compute Duty
          </CardTitle>
          <CardDescription>
            Select a row on the left, then enter required inputs.
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

              {/* Inputs */}
              {pureAdValorem ? (
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-1">
                    <Label>Declared Value ($)</Label>
                    <Input
                      value={declaredValue}
                      onChange={(e) => setDeclaredValue(e.target.value)}
                      placeholder="e.g. 1000"
                      inputMode="decimal"
                    />
                  </div>
                </div>
              ) : pureSpecific ? (
                <div className="grid grid-cols-3 gap-4">
                  {specificUnits.map((u) => (
                    <div className="col-span-1" key={u}>
                      <Label>Quantity ({u})</Label>
                      <Input
                        value={specificQty[u] ?? ""}
                        onChange={(e) =>
                          setSpecificQty((prev) => ({ ...prev, [u]: e.target.value }))
                        }
                        placeholder={`e.g. ${u === "each" ? "200" : "1000"}`}
                        inputMode="decimal"
                      />
                    </div>
                  ))}
                </div>
              ) : cascading ? (
                <>
                  <div className="flex flex-wrap gap-2 mb-2">
                    <NeedBadge>Needs Quantity (per specific unit)</NeedBadge>
                    <NeedBadge>% applied after specifics</NeedBadge>
                    {needsQualifierDVs && <NeedBadge>Also needs qualifier DVs</NeedBadge>}
                  </div>

                  {/* per-unit quantities: 1 field if single-specific, 2+ if multi-specific */}
                  <div className="grid grid-cols-3 gap-4">
                    {specificUnits.map((u) => (
                      <div className="col-span-1" key={u}>
                        <Label>Quantity ({u})</Label>
                        <Input
                          value={specificQty[u] ?? ""}
                          onChange={(e) =>
                            setSpecificQty((prev) => ({ ...prev, [u]: e.target.value }))
                          }
                          placeholder={`e.g. ${u === "each" ? "200" : "1000"}`}
                          inputMode="decimal"
                        />
                      </div>
                    ))}
                  </div>

                  {/* show DV inputs only for qualified % lines (if any) */}
                  {needsQualifierDVs && (
                    <div className="grid grid-cols-3 gap-4 mt-2">
                      {percentQuals.map((rawQ) => (
                        <div className="col-span-1" key={rawQ}>
                          <Label>Declared Value ({prettyQualifier(rawQ)})</Label>
                          <Input
                            value={qualifierValues[rawQ] ?? ""}
                            onChange={(e) =>
                              setQualifierValues((prev) => ({ ...prev, [rawQ]: e.target.value }))
                            }
                            placeholder="e.g. 100.00"
                            inputMode="decimal"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                // non-cascade: either pure specific or qualified % only, etc.
                <>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {hasSpecific && <NeedBadge>Needs Quantity</NeedBadge>}
                    {needsQualifierDVs && <NeedBadge>Needs Declared Value(s) by qualifier</NeedBadge>}
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    {hasSpecific && (
                      <div className="col-span-1">
                        <Label>Quantity</Label>
                        <Input
                          value={quantity}
                          onChange={(e) => setQuantity(e.target.value)}
                          placeholder="e.g. 200"
                          inputMode="decimal"
                        />
                      </div>
                    )}
                  </div>

                  {needsQualifierDVs && (
                    <div className="grid grid-cols-3 gap-4 mt-2">
                      {percentQuals.map((rawQ) => (
                        <div className="col-span-1" key={rawQ}>
                          <Label>Declared Value ({prettyQualifier(rawQ)})</Label>
                          <Input
                            value={qualifierValues[rawQ] ?? ""}
                            onChange={(e) =>
                              setQualifierValues((prev) => ({ ...prev, [rawQ]: e.target.value }))
                            }
                            placeholder="e.g. 100.00"
                            inputMode="decimal"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}

              <Button className="w-full" onClick={onCompute} disabled={computing}>
                {computing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Computing…
                  </>
                ) : (
                  "Compute Duty"
                )}
              </Button>

              {computeRes && (
                <Alert className="mt-2">
                  <Terminal className="h-4 w-4" />
                  <AlertTitle>Duty</AlertTitle>
                  <AlertDescription className="font-mono">
                    <div> Total Duty: ${Number(computeRes.totalDuty).toFixed(2)} </div>
                    {Array.isArray(computeRes.breakdown) && computeRes.breakdown.length > 0 && (
                      <div className="mt-1">
                        {computeRes.breakdown.map((c, i) => (
                          <div key={i}>
                            • {c.kind}: duty={fmtMoney(c.dutyAmount)} | adVal=
                            {c.adValorem ?? 0} | spec=
                            {c.specificPerUnit ?? 0} {displayUnitForUI(selected?.mfnTextRate, c.unit)} {c.qualifier ?? ""}
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
function useDebounce(value, delayMs = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return v;
}

function toDecimalOrZero(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : 0;
}
function toDecimalOrNull(x) {
  if (x === "" || x == null) return null;   // ← treat empty as null
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

function fmtMoney(x) {
  const n = Number(x);
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : "$0.00";
}

/** display-only shortener; NEVER use as key */
function prettyQualifier(q) {
  const firstComma = q.split(",")[0];
  const firstOr = firstComma.split(" or ")[0];
  return firstOr.trim();
}

/** Map a UI unit to what the backend parser expects (special-casing /line/ gross). */
function uiUnitToBackendUnit(rateText, uiUnit) {
  const t = (rateText || "").toLowerCase();
  if (uiUnit === "/gross" && /\/\s*line\s*\/\s*gross/.test(t)) {
    return "/line";
  }
  return uiUnit;
}

/** Parse flags + RAW % qualifiers + list of SPECIFIC unit tokens */
function parseParts(rateText) {
  if (!rateText)
    return {
      hasSpecific: false,
      hasPercent: false,
      percentQuals: [],
      hasUnqualifiedPercent: false,
      specificUnits: [],
    };

  const parts = rateText
    .split("+")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);

  const looksSpecific = (s) =>
    /\$/.test(s) ||
    /\bcent(s)?\b/.test(s) ||
    /¢/.test(s) ||
    /\/\s*[\w\d]+/.test(s) ||
    /\beach\b/.test(s);

  const hasSpecific = parts.some(looksSpecific);
  const hasPercent = parts.some((s) => /%|\bad\s*valorem\b/.test(s));
  
  // collect specific units
  const units = new Set();
  for (const p of parts) {
    if (looksSpecific(p)) {
      const slash = p.match(/\/\s*([a-z0-9.\-]+)/gi);
      if (slash) {
        slash.forEach((m) => {
          const tok = "/" + m.split("/")[1].trim();
          units.add(tok);
        });
      }
      if (/\beach\b/.test(p)) units.add("each");
      if (/\bjewel(s)?\b/.test(p) && !Array.from(units).includes("/jewel")) units.add("/jewel");
      if (/\bdoz(en)?\b/.test(p) && !Array.from(units).includes("/doz")) units.add("/doz");
    }
  }

  // --- UI normalization: collapse "/line/ gross" to just "/gross"
  const text = rateText.toLowerCase();
  if (/\/\s*line\s*\/\s*gross/.test(text)) {
    units.delete("/line");
    units.add("/gross");
  }

  // % qualifiers
  const percentQuals = [];
  let hasUnqualifiedPercent = false;

  for (const p of parts) {
    if (/%|\bad\s*valorem\b/.test(p)) {
      // grab everything from "on/of ..." to the end of THIS part
      const m = p.match(/\b(?:on|of)\s+(?:the\s+)?.*$/i);
      if (m) {
        const raw = m[0].trim();
        if (raw && !percentQuals.includes(raw)) percentQuals.push(raw);
      } else {
        hasUnqualifiedPercent = true;
      }
    }
  }
  return {
    hasSpecific,
    hasPercent,
    percentQuals,
    hasUnqualifiedPercent,
    specificUnits: Array.from(units),
  };
}

function NeedBadge({ children }) {
  return (
    <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium">
      {children}
    </span>
  );
}

function displayUnitForUI(rateText, unit) {
  const t = (rateText || "").toLowerCase();
  if (unit === "/line" && /\/\s*line\s*\/\s*gross/.test(t)) {
    return "/gross";
  }
  return unit ?? "";
}

function isIntegerLike(str) {
  return /^\d+$/.test(str.trim());
}