import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {calculateTariff,getAllPartnerCountries,getAllReporterCountries,getPartnersByTo,getReportersFrom,searchTariff,} from "@/api/axiosClient";
import { Button } from "@/components/ui/button";
import {Card,CardContent,CardFooter,CardHeader,CardTitle,CardDescription,} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue,} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Search, Calculator } from "lucide-react";
import { Relogin } from "@/components/Relogin";

const NONE = "none";

export default function TariffCalc() {
    // Get tariffId from query string
    const location = useLocation();
    const [autoSelectId, setAutoSelectId] = useState(null);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const tid = params.get("tariffId");
        setAutoSelectId(tid);
    }, [location.search]);

    const [showRelogin, setShowRelogin] = useState(false);

    // Countries
    const [fromOptions, setFromOptions] = useState([]);
    const [toOptions, setToOptions] = useState([]);
    const [fromId, setFromId] = useState(NONE);
    const [toId, setToId] = useState(NONE);
    const [loadingCountries, setLoadingCountries] = useState(false);

    // Search
    const [q, setQ] = useState("");
    const [page, setPage] = useState(0);
    const [size, setSize] = useState(10);
    const [searching, setSearching] = useState(false);
    const [searchError, setSearchError] = useState("");
    const [results, setResults] = useState({ content: [], totalPages: 0, number: 0, size: 10,last: null,});
    const [searchTick, setSearchTick] = useState(0);

    // Selection + compute
    const [selected, setSelected] = useState(null);
    const [declaredValue, setDeclaredValue] = useState("");
    const [quantity, setQuantity] = useState("");
    const [computing, setComputing] = useState(false);
    const [computeError, setComputeError] = useState("");
    const [computeRes, setComputeRes] = useState(null); // we use only the total for the last line

    // Workings visibility (no toggle; just show after compute)
    const [showWorkings, setShowWorkings] = useState(false);

    // Debounce q
    const debouncedQ = useDebounce(q, 300);
    const prevDQRef = useRef(debouncedQ);

    /** Helpers to load country lists */
    const loadAllFrom = async () => {
        setLoadingCountries(true);
        try {
            const { data } = await getAllPartnerCountries();
            setFromOptions(data || []);
        } catch (e) {
            if (e?.response?.status === 401) { setShowRelogin(true); return; }
            console.error(e);
        } finally { setLoadingCountries(false); }
    };
    const loadAllTo = async () => {
        setLoadingCountries(true);
        try {
            const { data } = await getAllReporterCountries();
            setToOptions(data || []);
        } catch (e) {
            if (e?.response?.status === 401) { setShowRelogin(true); return; }
            console.error(e);
        } finally { setLoadingCountries(false); }
    };

    /** Load both lists initially so either side can be chosen first */
    useEffect(() => {
        loadAllFrom();
        loadAllTo();
    }, []);

    /** When FROM changes */
    useEffect(() => {
        setSelected(null);
        setResults({ content: [], totalPages: 0, number: 0, size, last: null });
        setComputeError("");
        setComputeRes(null);
        setShowWorkings(false);
        setDeclaredValue("");
        setQuantity("");
        setPage(0);

        if (!fromId || fromId === NONE) { loadAllTo(); return; }

        const loadReporters = async () => {
            setLoadingCountries(true);
            try {
                const { data } = await getReportersFrom(fromId);
                setToOptions(data || []);
            } catch (e) {
                if (e?.response?.status === 401) { setShowRelogin(true); return; }
                console.error(e);
            } finally { setLoadingCountries(false); }
        };
        loadReporters();
    }, [fromId]);

    /** When TO changes */
    useEffect(() => {
        setSelected(null);
        setResults({ content: [], totalPages: 0, number: 0, size, last: null });
        setComputeError("");
        setComputeRes(null);
        setShowWorkings(false);
        setDeclaredValue("");
        setQuantity("");
        setPage(0);

        if (!toId || toId === NONE) { loadAllFrom(); return; }

        const loadPartnersByTo = async () => {
            setLoadingCountries(true);
            try {
                const { data } = await getPartnersByTo(toId);
                setFromOptions(data || []);
            } catch (e) {
                if (e?.response?.status === 401) { setShowRelogin(true); return; }
                console.error(e);
            } finally { setLoadingCountries(false); }
        };
        loadPartnersByTo();
    }, [toId]);

    /** Search */
    useEffect(() => {
        // reset to page 0 when typing new text
        if (prevDQRef.current !== debouncedQ && page !== 0) {
            setPage(0);
            prevDQRef.current = debouncedQ;
            return;
        }
        prevDQRef.current = debouncedQ;

        const fetchPage = async () => {
            setSearching(true);
            setSearchError("");
            try {
                const params = new URLSearchParams();
                params.set("page", String(page));
                params.set("size", String(size));
                if (fromId && fromId !== NONE) params.set("fromId", String(fromId));
                if (toId && toId !== NONE) params.set("toId", String(toId));
                const dQ = debouncedQ.trim();
                if (dQ !== "") params.set("q", dQ);

                const { data } = await searchTariff(params);

                // normalize paging (Page or Slice)
                const totalPages = Number.isFinite(Number(data?.totalPages))
                    ? Number(data.totalPages)
                    : Number.isFinite(Number(data?.totalElements))
                        ? Math.max(1, Math.ceil(Number(data.totalElements) / Number(data?.size ?? size)))
                        : 1;

                const normalized = {
                    content: Array.isArray(data?.content) ? data.content : [],
                    number: Number(data?.number ?? 0),
                    size: Number(data?.size ?? size),
                    totalPages: Number(totalPages),
                    last: data?.last ?? null,
                };

                if (normalized.totalPages > 0 && page >= normalized.totalPages) {
                    setPage(normalized.totalPages - 1);
                    return;
                }

                setResults(normalized);

                // auto-select by query param
                if (autoSelectId && normalized.content.length > 0) {
                    const found = normalized.content.find(
                        (row) => String(row.id ?? row.tariffId ?? row.tariffid) === String(autoSelectId)
                    );
                    if (found) {
                        const normalizedTariff = {
                            id: found.id ?? found.tariffId ?? found.tariffid,
                            descriptionwcountry: found.descriptionwcountry ?? found.descriptionWCountry ?? found.description,
                            category: found.category,
                            advalorem: found.advalorem ?? found.adValorem,
                            specificperunit: found.specificperunit ?? found.specificPerUnit,
                            unitname: found.unitname ?? found.unitName,
                        };
                        setSelected(normalizedTariff);
                    }
                }
            } catch (e) {
                if (e?.response?.status === 401) { setShowRelogin(true); return; }
                setSearchError("Search failed. Check /api/v1/tariffs/search and params.");
                console.error(e);
            } finally { setSearching(false); }
        };

        fetchPage();
    }, [fromId, toId, debouncedQ, page, size, searchTick, autoSelectId]);

    /** Reset inputs when selecting a new row */
    useEffect(() => {
        if (!selected) return;
        setDeclaredValue("");
        setQuantity("");
        setComputeError("");
        setComputeRes(null);
        setShowWorkings(false);
    }, [selected?.id]);

    /** Compute */
    const onCompute = async () => {
        if (!selected?.id) return;
        setComputing(true);
        setComputeError("");
        setComputeRes(null);
        setShowWorkings(false);

        try {
            const payload = {
                tariffId: selected.id,
                customsValue: toNumberOrNull(declaredValue),
                quantity: toNumberOrNull(quantity),
            };
            const { data } = await calculateTariff(payload);
            setComputeRes(data);     // we will use its total for the last line
            setShowWorkings(true);   // reveal workings block
        } catch (e) {
            if (e?.response?.status === 401) { setShowRelogin(true); return; }
            setComputeError("Compute failed. Check /api/v1/tariffs/calc.");
            console.error(e);
        } finally {
            setComputing(false);
        }
    };

    // Which inputs are needed (align with backend)
    const cat = (selected?.category || "").toUpperCase();
    const needsDV = cat === "AD_VALOREM"; // composite doesn't need customs value per your backend
    const needsQty = cat === "SPECIFIC_PER_UNIT" || cat === "COMPOSITE";

    // paging
    const pageIdx = Math.max(0, Number(results?.number ?? 0));
    const totalPages = Math.max(1, Number(results?.totalPages ?? 1));
    const canPrev = pageIdx > 0;
    const canNext = results?.last === false || pageIdx + 1 < totalPages;

    // numbers for rendering (only for the lines; final number is backend)
    const avDec = toNumberOrNull(selected?.advalorem);   // e.g. 0.05
    const avPct = avDec != null ? avDec * 100 : null;    // 5
    const avMult = avDec != null ? 1 + avDec : null;     // 1.05
    const sp = toNumberOrNull(selected?.specificperunit);
    const unit = selected?.unitname || "unit";
    const dvNum = toNumberOrNull(declaredValue);
    const qtyNum = toNumberOrNull(quantity);

    // ✅ compute intermediates safely for display
    const specPart =
        (cat === "SPECIFIC_PER_UNIT" || cat === "COMPOSITE") && qtyNum != null && sp != null
            ? qtyNum * sp
            : null;

    // backend total (for last line only)
    const backendTotal = Number(
        (computeRes?.total ?? computeRes?.totalDuty ?? computeRes?.calculatedValue)
    );
    const hasBackendTotal = Number.isFinite(backendTotal);

    return (
        <>
            {showRelogin && <Relogin />}
            <div className="grid gap-6 md:grid-cols-2">
                {/* Search Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Search className="h-5 w-5" />
                            Find Tariffs
                        </CardTitle>
                        <CardDescription>
                            Pick origin/destination, optionally add text, then search.
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-4">
                        {/* From / To row */}
                        <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label>From Country (origin)</Label>
                                <Select value={String(fromId)} onValueChange={(v) => { setFromId(v); setPage(0); }}>
                                    <SelectTrigger>
                                        <SelectValue placeholder={loadingCountries ? "Loading…" : "Select country"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={NONE}>None</SelectItem>
                                        {fromOptions.filter((c) => c?.countryId != null).map((c) => (
                                            <SelectItem key={c.countryId} value={String(c.countryId)}>
                                                {c.name} ({c.iso2})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>To Country (destination)</Label>
                                <Select value={String(toId)} onValueChange={(v) => { setToId(v); setPage(0); }}>
                                    <SelectTrigger>
                                        <SelectValue placeholder={loadingCountries ? "Loading…" : "Select country"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={NONE}>None</SelectItem>
                                        {toOptions.filter((c) => c?.countryId != null).map((c) => (
                                            <SelectItem key={c.countryId} value={String(c.countryId)}>
                                                {c.name} ({c.iso2})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        {/* Query + page size + Search */}
                        <div className="grid grid-cols-12 gap-4 items-end">
                            <div className="col-span-7">
                                <Label>Search by description / ID</Label>
                                <Input placeholder="e.g., Electronics" value={q} onChange={(e) => setQ(e.target.value)} />
                            </div>
                            <div className="col-span-2">
                                <Label>Page size</Label>
                                <Select value={String(size)} onValueChange={(v) => { setSize(Number(v)); setPage(0); }}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="10">10</SelectItem>
                                        <SelectItem value="20">20</SelectItem>
                                        <SelectItem value="50">50</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="col-span-3 flex items-end justify-end">
                                <Button className="w-full" onClick={() => setSearchTick((n) => n + 1)} disabled={searching}>
                                    {searching ? (<><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Searching…</>) : "Search"}
                                </Button>
                            </div>
                        </div>

                        {/* Results */}
                        <div className="border rounded-md divide-y">
                            {results.content.length === 0 && !searching && (
                                <div className="p-4 text-sm text-muted-foreground">No results.</div>
                            )}
                            {results.content.map((row) => {
                                const id = row.id ?? row.tariffId ?? row.tariffid;
                                const normalized = {
                                    id,
                                    descriptionwcountry: row.descriptionwcountry ?? row.descriptionWCountry ?? row.description,
                                    category: row.category,
                                    advalorem: row.advalorem ?? row.adValorem,
                                    specificperunit: row.specificperunit ?? row.specificPerUnit,
                                    unitname: row.unitname ?? row.unitName,
                                };
                                return (
                                    <button
                                        key={id}
                                        className={`w-full text-left p-3 hover:bg-muted/50 ${selected?.id === id ? "bg-muted/70" : ""}`}
                                        onClick={() => setSelected(normalized)}
                                    >
                                        <div className="flex justify-between">
                                            <div className="font-medium">ID: {id}</div>
                                            <div className="text-xs">{(normalized.category || "").toString()}</div>
                                        </div>
                                        <div className="text-sm text-muted-foreground">{normalized.descriptionwcountry}</div>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Pagination */}
                        <div className="flex justify-between items-center">
                            <Button variant="outline" disabled={!canPrev} onClick={() => setPage((p) => Math.max(0, p - 1))}>
                                Prev
                            </Button>
                            <div className="text-sm">Page {pageIdx + 1} / {totalPages}</div>
                            <Button variant="outline" disabled={!canNext} onClick={() => setPage((p) => p + 1)}>
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
                        <CardDescription>Select a tariff on the left, then enter required inputs.</CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-4">
                        {!selected ? (
                            <div className="text-sm text-muted-foreground">Select a tariff from search results.</div>
                        ) : (
                            <>
                                <div className="text-sm">
                                    <div className="font-medium">ID: {selected.id}</div>
                                    <div className="text-muted-foreground">{selected.descriptionwcountry}</div>
                                    {/* Rate summary (shows before compute) */}
                                    <div className="mt-1 text-xs text-muted-foreground">
                                        <span className="font-medium">Rate:</span> {rateSummary(selected) || "—"}
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-4">
                                    {needsDV && (
                                        <div className="col-span-1">
                                            <Label>Declared Value ($)</Label>
                                            <Input
                                                value={declaredValue}
                                                onChange={(e) => setDeclaredValue(e.target.value)}
                                                placeholder="e.g. 1000"
                                                inputMode="decimal"
                                            />
                                        </div>
                                    )}
                                    {needsQty && (
                                        <div className="col-span-1">
                                            <Label>Quantity{selected.unitname ? ` (${selected.unitname})` : ""}</Label>
                                            <Input
                                                value={quantity}
                                                onChange={(e) => setQuantity(e.target.value)}
                                                placeholder="e.g. 200"
                                                inputMode="decimal"
                                            />
                                        </div>
                                    )}
                                </div>

                                <Button
                                    className="w-full"
                                    onClick={onCompute}
                                    disabled={
                                        computing ||
                                        (needsDV && (declaredValue.trim() === "" || isNaN(Number(declaredValue)) || !Number.isFinite(Number(declaredValue)) || Number(declaredValue) <= 0)) ||
                                        (needsQty && (quantity.trim() === "" || isNaN(Number(quantity)) || !Number.isFinite(Number(quantity)) || Number(quantity) <= 0))
                                    }
                                >
                                    {computing ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Computing…</>) : ("Compute Duty")}
                                </Button>

                                {/* WORKINGS — final number comes from backendTotal */}
                                {showWorkings && (
                                    <div className="mt-3 bg-zinc-900 text-white rounded-lg p-4 font-mono text-sm whitespace-pre-wrap">
                                        <div>Tariff ID: {selected.id}</div>
                                        <div>Category: {cat}</div>

                                        {/* AD_VALOREM (backend: total = DeclaredValue × (1 + rate)) */}
                                        {cat === "AD_VALOREM" && avDec != null && dvNum != null && (
                                            <>
                                                <div>Ad Valorem Rate: {fmtPct(avPct)} (multiplier = 1 + {fmt(avDec)} = {fmt(avMult)})</div>
                                                <div> </div>
                                                <div>Total = Declared Value × (1 + rate)</div>
                                                <div>= ${fmt(dvNum)} × {fmt(avMult)}</div>
                                                <div>= {hasBackendTotal ? `$${fmt(backendTotal)}` : "—"}</div>
                                            </>
                                        )}

                                        {/* SPECIFIC_PER_UNIT (backend: total = Quantity × Rate per unit) */}
                                        {cat === "SPECIFIC_PER_UNIT" && sp != null && qtyNum != null && (
                                            <>
                                                <div>Specific Rate: ${fmt(sp)} per {unit}</div>
                                                <div> </div>
                                                <div>Total = Quantity × Rate per {unit}</div>
                                                <div>= {fmt(qtyNum)} × ${fmt(sp)} / {unit}</div>
                                                <div>= {hasBackendTotal ? `$${fmt(backendTotal)}` : "—"}</div>
                                            </>
                                        )}

                                        {/* COMPOSITE (backend: total = (Quantity × Rate) × (1 + rate)) */}
                                        {cat === "COMPOSITE" && sp != null && qtyNum != null && avDec != null && (
                                            <>
                                                <div>Specific Rate: ${fmt(sp)} per {unit}</div>
                                                <div>Ad Valorem Rate: {fmtPct(avPct)} (multiplier = 1 + {fmt(avDec)} = {fmt(avMult)})</div>
                                                <div> </div>

                                                {/* Step 1 — show the computed specific part number */}
                                                <div>Step 1 — Specific Part = Quantity × Rate per {unit}</div>
                                                <div>= {fmt(qtyNum)} × ${fmt(sp)} / {unit}</div>
                                                <div>= ${fmt(specPart)}</div>
                                                <div> </div>

                                                {/* Step 2 — show the multiplication with the multiplier, then the backend total */}
                                                <div>Step 2 — Apply Ad Valorem Multiplier</div>
                                                <div>Total = Specific Part × (1 + rate)</div>
                                                <div>= ${fmt(specPart)} × {fmt(avMult)}</div>
                                                <div>= {hasBackendTotal ? `$${fmt(backendTotal)}` : "—"}</div>
                                            </>
                                        )}
                                    </div>
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
        </>
    );
}

/* ------------ helpers (JS) ------------ */
function useDebounce(value, delayMs = 300) {
    const [v, setV] = useState(value);
    useEffect(() => {
        const id = setTimeout(() => setV(value), delayMs);
        return () => clearTimeout(id);
    }, [value, delayMs]);
    return v;
}

function toNumberOrNull(x) {
    if (x === "" || x == null) return null;
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
}

function fmt(n) {
    const x = Number(n ?? 0);
    return x.toFixed(2);
}

function fmtPct(n) {
    if (n == null) return "";
    const s = (Number(n).toFixed(2)).replace(/\.00$/, "");
    return `${s}%`;
}

/** Rate summary under description */
function rateSummary(selected) {
    if (!selected) return "";
    const category = String(selected?.category || "").toUpperCase();
    const avDec = toNumberOrNull(selected?.advalorem);
    const sp = toNumberOrNull(selected?.specificperunit);
    const unit = selected?.unitname || "unit";

    if (category === "AD_VALOREM" && avDec != null) return `${fmtPct(avDec * 100)} ad valorem`;
    if (category === "SPECIFIC_PER_UNIT" && sp != null) return `$${fmt(sp)} per ${unit}`;
    if (category === "COMPOSITE") {
        const parts = [];
        if (avDec != null) parts.push(`${fmtPct(avDec * 100)} ad valorem`);
        if (sp != null) parts.push(`$${fmt(sp)} per ${unit}`);
        return parts.join(" + ");
    }
    return "";
}
