import { useState, useEffect } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card.jsx";
import { Button } from "../components/ui/button.jsx";
import { Input } from "../components/ui/input.jsx";
import { Label } from "../components/ui/label.jsx";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert.jsx";
import { Terminal, Waves } from "lucide-react";
import CountrySelector from "../components/CountrySelector.jsx";
import { Spinner } from "../components/ui/shadcn-io/spinner/index.jsx";
import { toast } from "sonner";

// Import API functions
import { getAllReporterCountries, getAllPartnerCountries } from "../api/axiosClient.js";
import { getHistoricalData } from "../api/axiosClient.js";

export default function HistoricalTariffExplorer() {
  // --- State Management ---
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- NEW: State for dynamic chart labels ---
  const [yAxisLabel, setYAxisLabel] = useState("Ad Valorem Duty (%)");
  const [plotCategory, setPlotCategory] = useState("Ad Valorem"); // 'Ad Valorem', 'Specific'
  
  // State for country dropdowns
  const [reporterCountries, setReporterCountries] = useState([]);
  const [partnerCountries, setPartnerCountries] = useState([]);

  // State for search inputs
  const [searchMode, setSearchMode] = useState("prefix"); // 'prefix' or 'params'
  const [prefixSearch, setPrefixSearch] = useState("");
  const [htsCode, setHtsCode] = useState("");
  const [selectedReporter, setSelectedReporter] = useState(null);
  const [selectedPartner, setSelectedPartner] = useState(null);

  // Fetch countries for dropdowns on component mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const [reporterRes, partnerRes] = await Promise.all([
          getAllReporterCountries(),
          getAllPartnerCountries(),
        ]);
        
        const reporters = reporterRes.data.map(c => ({ value: c.countryId, label: c.name }));
        const partners = partnerRes.data.map(c => ({ value: c.countryId, label: c.name }));
        
        setReporterCountries(reporters);
        setPartnerCountries(partners);

      } catch (err) {
        console.error("Failed to fetch countries:", err);
        toast.error("Failed to load country lists.", {
          description: "Please refresh the page to try again."
        });
      }
    };
    fetchCountries();
  }, []);

  // --- Data Fetching ---
  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setData([]);
    // Reset labels to default
    setYAxisLabel("Ad Valorem Duty (%)");
    setPlotCategory("Ad Valorem");

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
        
        // --- THIS IS THE FIX ---
        // Inspect the first data point to determine the chart type
        const firstPoint = response.data[0];
        let formattedData = [];

        if (firstPoint.category === 'SPECIFIC_PER_UNIT') {
          setYAxisLabel(`Specific Duty (${firstPoint.unitname || 'USD'})`);
          setPlotCategory('Specific');
          formattedData = response.data.map(item => ({
            ...item, // Keep all original data for the tooltip
            year: Number(item.year),
            plotValue: parseFloat(item.specificperunit) || 0.0, // Plot this value
          }));
          toast.info("Displaying Specific Duty.");

        } else if (firstPoint.category === 'COMPOSITE') {
          setYAxisLabel("Ad Valorem Component (%)");
          setPlotCategory('Ad Valorem'); // Plot the ad valorem part
          formattedData = response.data.map(item => ({
            ...item,
            year: Number(item.year),
            plotValue: parseFloat(item.advalorem) || 0.0, // Plot this value
          }));
          toast.info("Composite tariff detected. Plotting Ad Valorem component.");
        
        } else {
          // Default to Ad Valorem (includes "Free", "Ad Valorem", or null categories)
          setYAxisLabel("Ad Valorem Duty (%)");
          setPlotCategory('Ad Valorem');
          formattedData = response.data.map(item => ({
            ...item,
            year: Number(item.year),
            plotValue: parseFloat(item.advalorem) || 0.0, // Plot this value
          }));
        }
        // --- END OF FIX ---

        setData(formattedData);
        toast.success(`Found ${formattedData.length} data points.`);
      } else {
        setData([]);
        toast.info("No data found for this query.", {
          description: "Please try a different search.",
        });
      }

    } catch (err) {
      console.error("Error fetching historical data:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Failed to fetch data";
      setError(errorMessage);
      toast.error("Search Failed", {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  // --- DYNAMIC CHART FORMATTERS ---
  
  // Format the Y-Axis ticks based on category
  const yAxisTickFormatter = (value) => {
    if (plotCategory === 'Specific') {
      return `${value.toFixed(4)}`; // e.g., "0.0065"
    }
    // Default to percentage
    return `${(value * 100).toFixed(0)}`; // e.g., "5"
  };

  // Format the Tooltip content
  const tooltipFormatter = (value, name, entry) => {
    // 'entry.payload' has the full, original data point
    const item = entry.payload; 
    
    if (name === "Trend") return null; // Hide trend line from tooltip

    switch (item.category) {
      case 'SPECIFIC_PER_UNIT':
        return [`${item.specificperunit || 0.0} ${item.unitname || 'USD'}`, "Specific Duty"];
      case 'COMPOSITE':
        const avp = (item.advalorem || 0) * 100;
        const spu = item.specificperunit || 0;
        return [`${avp.toFixed(2)}% + ${spu} ${item.unitname || 'USD'}`, "Composite Duty"];
      case 'FREE':
        return ["0.00%", "Free"];
      case 'AD_VALOREM':
      default:
        return [`${(item.advalorem * 100).toFixed(2)}%`, "Ad Valorem Duty"];
    }
  };

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
          {/* --- Search Mode Toggle --- */}
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

          {/* --- Search Input Fields --- */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {searchMode === "prefix" ? (
              // --- Mode 1: Prefix Search ---
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
              // --- Mode 2: Parameter Search ---
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

      {/* --- Chart Display --- */}
      <Card>
        <CardHeader>
          <CardTitle>Tariff Data Over Time</CardTitle>
          <CardDescription>
            {yAxisLabel} by year.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Loading State */}
          {loading && (
            <div className="flex justify-center items-center h-96">
              <Spinner size="large" />
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <Alert variant="destructive" className="h-96">
              <Terminal className="h-4 w-4" />
              <AlertTitle>Error Fetching Data</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Empty State */}
          {!loading && !error && data.length === 0 && (
            <div className="flex flex-col justify-center items-center h-96 text-center text-muted-foreground">
              <Waves className="h-12 w-12 mb-4" />
              <p className="text-lg font-medium">No data to display</p>
              <p>Please enter your search parameters above to get started.</p>
            </div>
          )}

          {/* Success State */}
          {!loading && !error && data.length > 0 && (
            <div className="h-96 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={data}
                  margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="year" 
                    label={{ value: 'Year', position: 'insideBottom', offset: -10 }}
                    padding={{ left: 20, right: 20 }}
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    tickCount={data.length < 10 ? data.length : 10}
                  />
                  <YAxis 
                    label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }}
                    unit={plotCategory === 'Ad Valorem' ? '%' : ''}
                    tickFormatter={yAxisTickFormatter}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                    formatter={tooltipFormatter}
                  />
                  <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '20px' }} />
                  {/* We plot 'plotValue' which is set to advalorem or specificperunit */}
                  <Bar dataKey="plotValue" name="Duty" barSize={20} fill="var(--theme-primary, #1E90FF)" />
                  <Line type="monotone" dataKey="plotValue" name="Trend" stroke="var(--theme-secondary, #FF6347)" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}