// src/pages/TariffCalcV2.jsx
import { useEffect, useRef, useState } from "react";
import axiosClient from "@/api/axiosClient";
import { Button } from "@/components/ui/button";
import {
    Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Search, Calculator, Terminal } from "lucide-react";
import { Relogin } from "@/components/Relogin";

/** ---- ENDPOINTS (adjust if your paths differ) ---- */
const URL_PARTNERS_ALL = "/countries/partners";                                   // origins that exist
const URL_REPORTERS_FROM = (fromPartnerId) => `/countries/reporters?fromId=${fromPartnerId}`; // destinations from origin
const URL_SEARCH = "/tariffs/search";
const URL_CALC = "/tariffs/calc";

// Sentinel used for "None" select option (can't be empty string with Radix)
const NONE = "none";

export default function TariffCalcV2() {
    const [showRelogin, setShowRelogin] = useState(false);

    // Countries
    const [fromOptions, setFromOptions] = useState([]); // partners (origins)
    const [toOptions, setToOptions] = useState([]);     // reporters (destinations from the origin)
    const [fromId, setFromId] = useState(NONE);         // <-- partnercountry
    const [toId, setToId] = useState(NONE);             // <-- reportercountry
    const [loadingCountries, setLoadingCountries] = useState(false);

    // Search
    const [q, setQ] = useState("");
    const [page, setPage] = useState(0);
    const [size, setSize] = useState(10);
    const [searching, setSearching] = useState(false);
    const [searchError, setSearchError] = useState("");
    const [results, setResults] = useState({ content: [], totalPages: 0, number: 0, size: 10 });
    const [searchTick, setSearchTick] = useState(0); // manual "Search" trigger

    // Selection + compute
    const [selected, setSelected] = useState(null);
    const [declaredValue, setDeclaredValue] = useState(""); // customsValue
    const [quantity, setQuantity] = useState("");
    const [computing, setComputing] = useState(false);
    const [computeError, setComputeError] = useState("");
    const [computeRes, setComputeRes] = useState(null);

    // Debounce q
    const debouncedQ = useDebounce(q, 300);
    const prevDQRef = useRef(debouncedQ);

    /** Load all possible origins (partners) */
    useEffect(() => {
        const loadPartners = async () => {
            setLoadingCountries(true);
            try {
                const { data } = await axiosClient.get(URL_PARTNERS_ALL);
                setFromOptions(data || []);
            } catch (e) {
                if (e.response?.status === 401) { setShowRelogin(true); return; }
                console.error(e);
            } finally {
                setLoadingCountries(false);
            }
        };
        loadPartners();
    }, []);

    /** When FROM (origin) changes, load destination options (reporters) */
    useEffect(() => {
        setToOptions([]);
        setToId(NONE);
        setSelected(null);
        setResults({ content: [], totalPages: 0, number: 0, size });
        setComputeRes(null);

        if (!fromId || fromId === NONE) return; // if "None", don't fetch reporters

        const loadReporters = async () => {
            setLoadingCountries(true);
            try {
                const { data } = await axiosClient.get(URL_REPORTERS_FROM(fromId));
                setToOptions(data || []);
            } catch (e) {
                if (e.response?.status === 401) { setShowRelogin(true); return; }
                console.error(e);
            } finally {
                setLoadingCountries(false);
            }
        };
        loadReporters();
    }, [fromId]);

    /** Search effect (auto + button) */
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

                // Map: fromId -> partnercountry, toId -> reportercountry
                if (fromId && fromId !== NONE) params.set("fromId", String(fromId));
                if (toId && toId !== NONE) params.set("toId", String(toId));

                const dQ = debouncedQ.trim();
                if (dQ !== "") params.set("q", dQ);

                const { data } = await axiosClient.get(`${URL_SEARCH}?${params.toString()}`);
                setResults(data);
            } catch (e) {
                if (e.response?.status === 401) { setShowRelogin(true); return; }
                setSearchError("Search failed. Check /api/v1/tariffs/search and your params (fromId=partnercountry, toId=reportercountry).");
                console.error(e);
            } finally {
                setSearching(false);
            }
        };

        // Always allow searching (even if no filters)
        fetchPage();
    }, [fromId, toId, debouncedQ, page, size, searchTick]);

    /** Reset compute inputs when selecting a new row */
    useEffect(() => {
        if (!selected) return;
        setDeclaredValue("");
        setQuantity("");
        setComputeRes(null);
        setComputeError("");
    }, [selected?.id]);

    /** Compute click */
    const onCompute = async () => {
        if (!selected?.id) return;
        setComputing(true);
        setComputeError("");
        setComputeRes(null);
        try {
            const payload = {
                tariffId: selected.id,
                customsValue: toNumberOrNull(declaredValue),
                quantity: toNumberOrNull(quantity),
            };
            const { data } = await axiosClient.post(URL_CALC, payload);
            setComputeRes(data);
        } catch (e) {
            if (e.response?.status === 401) { setShowRelogin(true); return; }
            setComputeError("Compute failed. Check /api/v1/tariffs/calc.");
            console.error(e);
        } finally {
            setComputing(false);
        }
    };

    // Derived input needs based on category
    const cat = (selected?.category || "").toUpperCase();
    const needsDV = cat === "AD_VALOREM";
    const needsQty = cat === "SPECIFIC_PER_UNIT" || cat === "COMPOSITE";

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
                        <CardDescription>Pick origin/destination, optionally add text, then search.</CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-4">
                        {/* From / To row */}
                        <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label>From Country (origin)</Label>
                                <Select
                                    value={String(fromId)}
                                    onValueChange={(v) => { setFromId(v); setPage(0); }}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={loadingCountries ? "Loading…" : "Select country"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={NONE}>None</SelectItem> {/* IMPORTANT: not "" */}
                                        {fromOptions
                                            .filter((c) => c?.countryId != null)
                                            .map((c) => (
                                                <SelectItem key={c.countryId} value={String(c.countryId)}>
                                                    {c.name} ({c.iso2})
                                                </SelectItem>
                                            ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>To Country (destination)</Label>
                                <Select
                                    value={String(toId)}
                                    onValueChange={(v) => { setToId(v); setPage(0); }}
                                    disabled={(fromId === NONE && toOptions.length === 0)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={!fromId || fromId === NONE ? "Select From or choose None" : (loadingCountries ? "Loading…" : "Select country")} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={NONE}>None</SelectItem>
                                        {toOptions
                                            .filter((c) => c?.countryId != null)
                                            .map((c) => (
                                                <SelectItem key={c.countryId} value={String(c.countryId)}>
                                                    {c.name} ({c.iso2})
                                                </SelectItem>
                                            ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        {/* Query + page size + Search button */}
                        <div className="grid grid-cols-12 gap-4 items-end">
                            <div className="col-span-7">
                                <Label>Search by description / ID</Label>
                                <Input
                                    placeholder="e.g., sunglasses"
                                    value={q}
                                    onChange={(e) => setQ(e.target.value)}
                                />
                            </div>
                            <div className="col-span-2">
                                <Label>Page size</Label>
                                <Select
                                    value={String(size)}
                                    onValueChange={(v) => { setSize(Number(v)); setPage(0); }}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="10">10</SelectItem>
                                        <SelectItem value="20">20</SelectItem>
                                        <SelectItem value="50">50</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="col-span-3 flex items-end justify-end">
                                <Button
                                    className="w-full"
                                    onClick={() => setSearchTick((n) => n + 1)}
                                    disabled={searching}
                                >
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
                                // normalize DTO vs entity field names
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
                                        <div className="text-sm text-muted-foreground">
                                            {normalized.descriptionwcountry}
                                        </div>
                                    </button>
                                );
                            })}
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
                                            <Label>
                                                Quantity{selected.unitname ? ` (${selected.unitname})` : ""}
                                            </Label>
                                            <Input
                                                value={quantity}
                                                onChange={(e) => setQuantity(e.target.value)}
                                                placeholder="e.g. 200"
                                                inputMode="decimal"
                                            />
                                        </div>
                                    )}
                                </div>

                                <Button className="w-full" onClick={onCompute} disabled={computing}>
                                    {computing ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Computing…</>) : ("Compute Duty")}
                                </Button>

                                {computeRes && (
                                    <Alert className="mt-2">
                                        <Terminal className="h-4 w-4" />
                                        <AlertTitle>Duty</AlertTitle>
                                        <AlertDescription className="font-mono">
                                            <div>Total Duty: ${Number(computeRes.total ?? computeRes.totalDuty ?? 0).toFixed(2)}</div>
                                            {Array.isArray(computeRes.breakdown) && computeRes.breakdown.length > 0 && (
                                                <div className="mt-1">
                                                    {computeRes.breakdown.map((c, i) => (
                                                        <div key={i}>• {c.kind}: ${Number(c.dutyAmount || 0).toFixed(2)}</div>
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
        </>
    );
}

/* ------------ helpers ------------ */
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

