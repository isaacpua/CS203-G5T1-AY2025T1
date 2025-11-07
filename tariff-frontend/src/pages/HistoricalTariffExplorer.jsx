import {ComposedChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend, ResponsiveContainer,} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Button } from "../components/ui/button.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert.jsx";
import { Terminal, Waves } from "lucide-react";
import CountrySelector from "../components/CountrySelector.jsx";
import { Spinner } from "../components/ui/shadcn-io/spinner/index.jsx";
import { toast } from "sonner";
import { useState, useEffect } from "react";

// Import API functions
import { getAllReporterCountries, getAllPartnerCountries } from "../api/axiosClient.js";
import { getHistoricalData } from "../api/axiosClient.js";

export default function HistoricalTariffExplorer() {
  // --- State Management ---
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- Dynamic chart labels ---
  const [yAxisLabel, setYAxisLabel] = useState("Ad Valorem Duty (%)");
  const [plotCategory, setPlotCategory] = useState("Ad Valorem"); // 'Ad Valorem', 'Specific'

  // Country dropdowns
  const [reporterCountries, setReporterCountries] = useState([]);
  const [partnerCountries, setPartnerCountries] = useState([]);

  // Search inputs
  const [searchMode, setSearchMode] = useState("prefix"); // 'prefix' or 'params'
  const [prefixSearch, setPrefixSearch] = useState("");
  const [htsCode, setHtsCode] = useState("");
  const [selectedReporter, setSelectedReporter] = useState(null);
  const [selectedPartner, setSelectedPartner] = useState(null);

  // Hover/lock state for the fixed info box
  const [point, setPoint] = useState(null);    // last hovered/clicked data point
  const [locked, setLocked] = useState(false); // click to lock/unlock the box


  // Headless tooltip: updates `point` whenever the hovered datum changes
  const GhostTooltip = ({ active, payload, onUpdate }) => {
    useEffect(() => {
      if (!onUpdate) return;
      if (active && payload && payload.length) {
        onUpdate(payload[0].payload);     // full datum
      } else {
        onUpdate(null);
      }
    }, [active, payload, onUpdate]);
    return null; // renders nothing
  };
  const toUnitSymbol = (u) => {
    const s = (u || "").toLowerCase();
    if (s.includes("kilo")) return "kg";
    if (s.includes("liter") || s.includes("litre")) return "L";
    if (s === "unit" || s.includes("unit")) return "unit";
    return u || "unit";
  };

  const prettyCat = (c) => (c ? String(c).toUpperCase() : "—");

  const valueText = (pt) => {
    if (!pt) return "";
    const cat = prettyCat(pt.category);
    const unitSym = toUnitSymbol(pt.unitname);

    if (cat === "FREE") return ""; // no number for FREE

    if (cat === "SPECIFIC_PER_UNIT") {
      const v = Number(pt.specificperunit || 0);
      return `$${v.toFixed(4)} / ${unitSym}`;
    }
    if (cat === "COMPOSITE") {
      const av = Number(pt.advalorem || 0) * 100;
      const sp = Number(pt.specificperunit || 0);
      return `${av.toFixed(2)}% + $${sp.toFixed(4)} / ${unitSym}`;
    }
    // AD_VALOREM (default)
    const av = Number(pt.advalorem || 0) * 100;
    return `${av.toFixed(2)}%`;
  };



  // Fetch countries for dropdowns on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const [reporterRes, partnerRes] = await Promise.all([
          getAllReporterCountries(),
          getAllPartnerCountries(),
        ]);
        const reporters = reporterRes.data.map((c) => ({ value: c.countryId, label: c.name }));
        const partners = partnerRes.data.map((c) => ({ value: c.countryId, label: c.name }));
        setReporterCountries(reporters);
        setPartnerCountries(partners);
      } catch (err) {
        console.error("Failed to fetch countries:", err);
        toast.error("Failed to load country lists.", { description: "Please refresh the page to try again." });
      }
    };
    fetchCountries();
  }, []);

  // --- Data Fetching ---
  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setData([]);
    setYAxisLabel("Ad Valorem Duty (%)");
    setPlotCategory("Ad Valorem");
    setPoint(null);
    setLocked(false);

    let params = {};
    try {
      if (searchMode === "prefix") {
        if (!prefixSearch || prefixSearch.length < 6) {
          throw new Error("Tariff ID Prefix must be at least 6 characters long.");
        }
        params = { full_tariff_id_prefix: prefixSearch.trim().toUpperCase() };
      } else {
        if (!htsCode || !selectedReporter || !selectedPartner) {
          throw new Error("Please fill out HTS Code, Reporter, and Partner fields.");
        }
        params = {
          hts6: htsCode.trim(),
          reporter_id: selectedReporter.value,
          partner_id: selectedPartner.value,
        };
      }

      const response = await getHistoricalData(params);

      if (response.data && response.data.length > 0) {
        let primaryCategory = "AD_VALOREM";
        let primaryUnitName = "USD";
        const firstPaidPoint = response.data.find((item) => item.category !== "FREE");
        if (firstPaidPoint) {
          primaryCategory = firstPaidPoint.category;
          primaryUnitName = firstPaidPoint.unitname || "USD";
        } else if (response.data.length > 0) {
          primaryCategory = "FREE";
        }

        let formattedData = [];
        if (primaryCategory === 'SPECIFIC_PER_UNIT') {
          const unitSym = toUnitSymbol(primaryUnitName);
          setYAxisLabel(`Specific Duty ($/${unitSym})`);
          setPlotCategory('Specific');
          formattedData = response.data.map(item => ({
            ...item,
            year: Number(item.year),
            plotValue: parseFloat(item.specificperunit) || 0.0,
          }));
          if (firstPaidPoint) toast.info("Displaying Specific Duty.");
        } else if (primaryCategory === "COMPOSITE") {
          setYAxisLabel("Ad Valorem (%)  ·  Specific ($/unit)");
          setPlotCategory('Composite'); // just a label; not used further

          formattedData = response.data.map(item => {
            const av = Number(item.advalorem || 0);          // fraction, e.g. 0.034
            const sp = Number(item.specificperunit || 0);     // dollars per unit
            return {
              ...item,
              year: Number(item.year),
              plotAV: av,            // LEFT axis (%)
              plotSP: sp,            // RIGHT axis ($/unit)
              unitname: item.unitname || 'unit',
            };
          });

          if (firstPaidPoint) toast.info("Composite: showing Ad Valorem (left) + Specific (right).");
        } else {
          setYAxisLabel("Ad Valorem Duty (%)");
          setPlotCategory("Ad Valorem");
          formattedData = response.data.map((item) => ({
            ...item,
            year: Number(item.year),
            plotValue: parseFloat(item.advalorem) || 0.0,
          }));
        }

        setData(formattedData);
        toast.success(`Found ${formattedData.length} data points.`);
      } else {
        setData([]);
        toast.info("No data found for this query.", { description: "Please try a different search." });
      }
    } catch (err) {
      console.error("Error fetching historical data:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Failed to fetch data";
      setError(errorMessage);
      toast.error("Search Failed", { description: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  // --- Formatters ---
  const pctTick = (v) => `${(v * 100).toFixed(2)}`;
  const moneyTick = (v) => `${v.toFixed(4)}`; // or toFixed(3/2) if you prefer
  const isComposite = data?.some(d => (d.category || d.Category || "").toUpperCase() === "COMPOSITE");
  const unitName = (data?.find(d => d.unitname)?.unitname || "unit").toLowerCase();

  // make denser grid for composite (left axis = ad valorem)
  let yLeftTicks = undefined;
  if (isComposite) {
    const avVals = data
      .map(d => Number(d.plotAV ?? d.advalorem ?? 0))
      .filter(n => Number.isFinite(n));
    const minAV = avVals.length ? Math.min(...avVals) : 0;
    const maxAV = avVals.length ? Math.max(...avVals) : 1;
    yLeftTicks = makeTicks(minAV, maxAV, 10); // ← more ticks = more gridlines
  }

  // a few more vertical gridlines too
  const xTickCount = isComposite ? 12 : 10;

  return (
    <div className="flex flex-col gap-8">
      <Card>
        <CardHeader>
          <CardTitle>Historical Tariff Explorer</CardTitle>
          <CardDescription>
            Search for historical tariff data directly from the primary database.
            Results are plotted by year and duty type.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Search Mode Toggle */}
          <div className="flex gap-2 rounded-md bg-muted p-1">
            <Button
              variant={searchMode === "prefix" ? "default" : "ghost"}
              className="flex-1"
              onClick={() => setSearchMode("prefix")}
            >
              Search by Tariff ID Prefix
            </Button>
            <Button
              variant={searchMode === "params" ? "default" : "ghost"}
              className="flex-1"
              onClick={() => setSearchMode("params")}
            >
              Search by Parameters
            </Button>
          </div>

          {/* Search Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {searchMode === "prefix" ? (
              <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div className="md:col-span-3">
                  <Label htmlFor="prefixSearch">Tariff ID Prefix (e.g., 170211USAU)</Label>
                  <Input
                    id="prefixSearch"
                    placeholder="Enter Tariff ID (e.g., 170211USAU)"
                    value={prefixSearch}
                    onChange={(e) => setPrefixSearch(e.target.value)}
                  />
                </div>
                <Button onClick={handleSearch} disabled={loading} className="w-full">
                  {loading ? <Spinner /> : "Search"}
                </Button>
              </div>
            ) : (
              <>
                <div>
                  <Label htmlFor="htsCode">6-Digit HTS Code</Label>
                  <Input
                    id="htsCode"
                    placeholder="e.g., 170211"
                    value={htsCode}
                    onChange={(e) => setHtsCode(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Reporter Country</Label>
                  <CountrySelector
                    countries={reporterCountries}
                    value={selectedReporter}
                    onChange={setSelectedReporter}
                    placeholder="Select Reporter..."
                  />
                </div>
                <div>
                  <Label>Partner Country</Label>
                  <CountrySelector
                    countries={partnerCountries}
                    value={selectedPartner}
                    onChange={setSelectedPartner}
                    placeholder="Select Partner..."
                  />
                </div>
                <Button onClick={handleSearch} disabled={loading} className="w-full md:self-end">
                  {loading ? <Spinner /> : "Search"}
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Tariff Data Over Time</CardTitle>
          <CardDescription>{yAxisLabel} by year.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading && (
            <div className="flex justify-center items-center h-96">
              <Spinner size="large" />
            </div>
          )}

          {error && !loading && (
            <Alert variant="destructive" className="h-96">
              <Terminal className="h-4 w-4" />
              <AlertTitle>Error Fetching Data</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!loading && !error && data.length === 0 && (
            <div className="flex flex-col justify-center items-center h-96 text-center text-muted-foreground">
              <Waves className="h-12 w-12 mb-4" />
              <p className="text-lg font-medium">No data to display</p>
              <p>Please enter your search parameters above to get started.</p>
            </div>
          )}

          {!loading && !error && data.length > 0 && (
            <div className="relative h-96 w-full">
              {/* Fixed top-center info panel with current point OR summary */}
              <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 -top-2 z-10">
                <div className="rounded border bg-card/90 px-3 py-1 text-xs shadow whitespace-nowrap">
                  {point ? (
                    <>
                      <span className="font-medium">Year {point.year}</span>{" "}
                      <span className="text-muted-foreground">• {prettyCat(point.category)}</span>
                      {valueText(point) ? <> • {valueText(point)}</> : null}
                    </>
                  ) : (
                    <>Hover over a point to see data</>
                  )}
                </div>
              </div>

              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={data}
                  margin={{ top: 28, right: 60, bottom: 30, left: 60 }}
                >
                  {/* inside <ComposedChart> */}
                  {isComposite ? (
                    <CartesianGrid horizontal vertical xAxisId="x" yAxisId="left"
                      stroke="var(--chart-grid)" strokeDasharray="3 3" />
                  ) : (
                    <CartesianGrid horizontal vertical
                      stroke="var(--chart-grid)" strokeDasharray="3 3" />
                  )}

                  <XAxis
                    dataKey="year"
                    type="number"
                    domain={["dataMin", "dataMax"]}
                    padding={{ left: 10, right: 20 }}
                    stroke="var(--chart-axis)"
                    tick={{ fill: "var(--chart-axis)" }}
                    label={{ value: "Year", position: "insideBottom", offset: -10, fill: "var(--chart-axis)" }}
                    tickCount={xTickCount}
                    tickMargin={8}
                  />

                  {!isComposite ? (
                    <>
                      {/* Single-axis (Ad Valorem OR Specific) */}
                      <YAxis
                        width={60}
                        tickMargin={8}
                        tickCount={6}
                        stroke="var(--chart-axis)"                 // axis line
                        tick={{ fill: "var(--chart-axis)" }}       // tick text
                        label={{
                          value: yAxisLabel,
                          angle: -90,
                          position: "left",
                          offset: 30,
                          dy: -100,
                          fill: "var(--chart-axis)",              // label text
                        }}
                        tickFormatter={plotCategory === "Ad Valorem" ? pctTick : moneyTick}
                        domain={["auto", "auto"]}
                      />
                      {/* Ghost tooltip updates `point` without rendering a popup */}
                      <Tooltip
                        cursor={false}
                        isAnimationActive={false}
                        content={<GhostTooltip onUpdate={locked ? undefined : setPoint} />}
                      />

                      <Legend verticalAlign="bottom" align="right" wrapperStyle={{ paddingTop: 10 }} />

                      <Line
                        type="monotone"
                        // prefer plotValue; fall back to plotAV/plotSP if present
                        dataKey={(d) =>
                          typeof d.plotValue === "number"
                            ? d.plotValue
                            : typeof d.plotAV === "number"
                              ? d.plotAV
                              : typeof d.plotSP === "number"
                                ? d.plotSP
                                : 0
                        }
                        name="Trend"
                        stroke="var(--chart-3, #3b82f6)"
                        dot={{ r: 2 }}
                        activeDot={{ r: 3 }}
                        isAnimationActive={false}
                      />
                    </>
                  ) : (
                    <>
                      {/* Dual-axis for COMPOSITE */}
                      <YAxis
                        yAxisId="left"
                        width={60}
                        tickMargin={8}
                        stroke="var(--chart-axis)"
                        tick={{ fill: "var(--chart-axis)" }}
                        label={{ value: "Ad Valorem (%)", angle: -90, position: "left", offset: 30, dy: -100, fill: "var(--chart-axis)" }}
                        ticks={yLeftTicks}  // ← explicit dense ticks drive gridlines
                        domain={["auto", "auto"]}
                        tickFormatter={(v) => (v * 100).toFixed(2)}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        tickCount={6}
                        width={70}
                        tickMargin={8}
                        label={{ value: `Specific ($/${unitName})`, angle: -90, position: "right", offset: 20, fill: "var(--chart-axis)" }}
                        tickFormatter={moneyTick}
                        domain={["auto", "auto"]}
                        stroke="var(--chart-axis)"                 // axis line
                        tick={{ fill: "var(--chart-axis)" }}       // tick text
                      />

                      <Tooltip
                        cursor={false}
                        isAnimationActive={false}
                        content={<GhostTooltip onUpdate={locked ? undefined : setPoint} />}
                      />

                      <Legend verticalAlign="bottom" align="right" wrapperStyle={{ paddingTop: 10 }} />

                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="plotAV"
                        name="Ad Valorem (%)"
                        stroke="var(--chart-3, #3b82f6)"
                        dot={{ r: 2 }}
                        activeDot={{ r: 4 }}
                        isAnimationActive={false}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="plotSP"
                        name={`Specific ($/${unitName})`}
                        stroke="var(--theme-secondary, #FF6347)"
                        strokeDasharray="4 4"
                        dot={{ r: 2 }}
                        activeDot={{ r: 4 }}
                        isAnimationActive={false}
                      />
                    </>
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function niceStep(stepRaw) {
  const p = Math.pow(10, Math.floor(Math.log10(stepRaw)));
  const err = stepRaw / p;
  if (err >= 7.5) return 10 * p;
  if (err >= 3.5) return 5 * p;
  if (err >= 1.5) return 2 * p;
  return 1 * p;
}
function makeTicks(min, max, desired = 8) {
  if (!isFinite(min) || !isFinite(max) || min === max) {
    const b = isFinite(min) ? min : 0;
    return [b - 1, b, b + 1];
  }
  const span = max - min;
  const step = niceStep(span / Math.max(2, desired));
  const niceMin = Math.floor(min / step) * step;
  const niceMax = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = niceMin; v <= niceMax + 1e-12; v += step) ticks.push(+v.toFixed(10));
  return ticks;
}
