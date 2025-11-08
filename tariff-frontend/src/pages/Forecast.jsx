import { getForecast, updateForecast } from "@/api/axiosClient";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Search, RefreshCw, Download } from "lucide-react";
import { Spinner } from "@/components/ui/shadcn-io/spinner";
import Papa from "papaparse";
import { useTheme } from "@/components/theme-provider";
// NEW: card shell
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function Forecast() {
  const [forecastData, setForecastData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [searchMethod, setSearchMethod] = useState("description");
  const [searchValue, setSearchValue] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [columnWidths, setColumnWidths] = useState({
    tariffid: 120,
    description: 300,
    unitname: 120,
    forecast_year: 120,
    forecast_advalorem: 150,
    forecast_specificperunit: 180,
    created_at: 120,
  });
  const [resizing, setResizing] = useState(null);
  const [contentVisible, setContentVisible] = useState(false);
  const { theme } = useTheme();
  const prefersDark =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = theme === "dark" || (theme === "system" && prefersDark);

  const fetchForecast = async (asRefresh = false) => {
    try {
      asRefresh ? setIsRefreshing(true) : setLoading(true);
      const response = await getForecast();

      const columns = response.data;
      const rowIds = Object.keys(columns.tariffid || {});
      const rows = [];

      for (const rowId of rowIds) {
        rows.push({
          tariffid: columns.tariffid?.[rowId],
          description: columns.description?.[rowId],
          unitname: columns.unitname?.[rowId],
          forecast_year: columns.forecast_year?.[rowId],
          forecast_advalorem: columns.forecast_advalorem?.[rowId],
          forecast_specificperunit: columns.forecast_specificperunit?.[rowId],
          created_at: columns.created_at?.[rowId],
        });
      }

      setForecastData(rows);
      setFilteredData(rows);

      if (asRefresh) {
        toast.success(`Loaded ${rows.length} forecast records`);
      }
    } catch (err) {
      toast.error("Failed to fetch forecast data", {
        description: err.message || "An error occurred while loading the data"
      });
      console.error("Error fetching forecast:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => { fetchForecast(false); }, []);

  useEffect(() => {
    let filtered = forecastData;

    if (searchValue) {
      const lowercaseSearch = searchValue.toLowerCase();
      filtered = filtered.filter((row) =>
        String(row[searchMethod]).toLowerCase().includes(lowercaseSearch)
      );
    }

    setFilteredData(filtered);
    setCurrentPage(1);
  }, [searchValue, searchMethod, forecastData]);

  useEffect(() => {
    const t = setTimeout(() => setContentVisible(true), 500);
    return () => clearTimeout(t);
  }, []);

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await updateForecast();
      fetchForecast(true);
    } catch (err) {
      console.log(err)
      toast.error("Failed to refresh forecast data", {
        description: err?.response?.data?.detail || "An error occurred while loading the data"
      });
      console.error("Error refreshing forecast:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      setIsExporting(true);

      const rows = filteredData.map((row) => ({
        "Tariff ID": row.tariffid ?? "",
        "Description": row.description ?? "",
        "Unit Name": row.unitname ?? "",
        "Forecast Year": row.forecast_year ?? "",
        "Ad Valorem": row.forecast_advalorem != null
          ? `${(row.forecast_advalorem * 100).toFixed(2)}%`
          : "",
        "Specific Per Unit": row.forecast_specificperunit != null
          ? `$${row.forecast_specificperunit.toFixed(2)}`
          : "",
        "Created At": row.created_at
          ? new Date(row.created_at).toISOString()
          : "",
      }));

      const csv = Papa.unparse(rows, { header: true, skipEmptyLines: true });
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `forecast_data_${new Date().toISOString()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);

      toast.success(`Exported ${rows.length} forecast records`);
    } catch (err) {
      console.error("Export error:", err);
      toast.error("Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleMouseDown = (columnName, e) => {
    setResizing({ columnName, startX: e.clientX, startWidth: columnWidths[columnName] });
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!resizing) return;
      const diff = e.clientX - resizing.startX;
      const newWidth = Math.max(50, resizing.startWidth + diff);
      setColumnWidths((prev) => ({
        ...prev,
        [resizing.columnName]: newWidth,
      }));
    };

    const handleMouseUp = () => setResizing(null);

    if (resizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [resizing]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div>Loading forecast data...</div>
        <Spinner />
      </div>
    );
  }

  const totalPages = Math.ceil(filteredData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const displayedRows = filteredData.slice(startIndex, endIndex);

  const searchMethodOptions = {
    tariffid: "Tariff ID",
    description: "Description",
    unitname: "Unit Name",
    forecast_year: "Forecast Year",
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-transparent">
      {/* Background video + darken layer */}
      <div className="fixed inset-0 z-10 pointer-events-none">
        <video
          autoPlay
          loop
          muted
          playsInline
          key={isDark ? "dark-video" : "light-video"} // ensures React reloads video when theme changes
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-1000 ${contentVisible ? "blur-sm scale-105" : "blur-0 scale-100"
            }`}
        >
          <source
            src={isDark ? "/Barn_Night.mp4" : "/Barn_Animation.mp4"}
            type="video/mp4"
          />
        </video>
        <div
          className={`absolute inset-0 bg-black/40 transition-opacity duration-1000 ${contentVisible ? "opacity-60" : "opacity-30"}`}
        />
      </div>

      {/* Foreground app content on a WHITE card, centered */}
      <div className="relative z-10">
        <TooltipProvider>
          <div className="max-w-7xl mx-auto w-full px-4 md:px-6 pt-20">
            {/* radius + clipping live here */}
            <Card className="mt-0 border-0 shadow-lg bg-white dark:bg-neutral-900 rounded-2xl overflow-hidden">
              {/* no rounded here; card clips the green band */}
              <CardHeader className="p-4 bg-green-50 dark:bg-green-900/20">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl md:text-2xl font-bold text-foreground">
                      Forecasts
                    </CardTitle>
                    <CardDescription className="text-sm md:text-base text-muted-foreground mt-1">
                      Manage and explore forecast data with advanced filtering capabilities
                    </CardDescription>
                  </div>

                  <div className="flex items-center gap-2">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleRefresh}
                          disabled={isRefreshing}
                        >
                          <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Refresh</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleExportCSV}
                          disabled={isExporting || filteredData.length === 0}
                        >
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
                  {/* Solid search panel */}
                  <div className="flex flex-col gap-2 p-4 bg-white dark:bg-neutral-900 rounded-xl border mb-3">
                    <div className="grid grid-cols-1 md:grid-cols-[200px_1fr_auto] gap-4 items-end">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Search Method</label>
                        <Select value={searchMethod} onValueChange={setSearchMethod}>
                          <SelectTrigger>
                            <div className="flex items-center gap-2">
                              <Search className="h-4 w-4" />
                              <SelectValue />
                            </div>
                          </SelectTrigger>
                          <SelectContent>
                            {Object.entries(searchMethodOptions).map(([value, label]) => (
                              <SelectItem key={value} value={value}>
                                {label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Search {searchMethodOptions[searchMethod]}</label>
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="e.g., electronics, beverages..."
                            value={searchValue}
                            onChange={(e) => setSearchValue(e.target.value)}
                            className="pl-9"
                          />
                        </div>
                      </div>

                      <div className="text-sm text-muted-foreground pb-2">
                        {filteredData.length} results
                      </div>
                    </div>
                  </div>

                  {/* Solid table surface */}
                  <div className="border rounded-xl bg-white dark:bg-neutral-900 overflow-hidden">
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent">
                            <TableHead style={{ width: columnWidths.tariffid, position: "relative" }} className="border-r font-bold">
                              Tariff ID
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("tariffid", e)}
                              />
                            </TableHead>
                            <TableHead style={{ width: columnWidths.description, position: "relative" }} className="border-r font-bold">
                              Description
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("description", e)}
                              />
                            </TableHead>
                            <TableHead style={{ width: columnWidths.unitname, position: "relative" }} className="border-r font-bold">
                              Unit Name
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("unitname", e)}
                              />
                            </TableHead>
                            <TableHead style={{ width: columnWidths.forecast_year, position: "relative" }} className="border-r font-bold">
                              Forecast Year
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("forecast_year", e)}
                              />
                            </TableHead>
                            <TableHead className="text-right border-r font-bold" style={{ width: columnWidths.forecast_advalorem, position: "relative" }}>
                              Ad Valorem
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("forecast_advalorem", e)}
                              />
                            </TableHead>
                            <TableHead className="text-right border-r font-bold" style={{ width: columnWidths.forecast_specificperunit, position: "relative" }}>
                              Specific/Unit
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("forecast_specificperunit", e)}
                              />
                            </TableHead>
                            <TableHead style={{ width: columnWidths.created_at, position: "relative" }} className="font-bold">
                              Created At
                              <div
                                className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary z-10"
                                onMouseDown={(e) => handleMouseDown("created_at", e)}
                              />
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {displayedRows.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={7} className="text-center h-24">
                                No forecast data available
                              </TableCell>
                            </TableRow>
                          ) : (
                            displayedRows.map((row, index) => (
                              <TableRow key={`${row.tariffid}-${row.forecast_year}-${index}`} className="hover:bg-muted/40">
                                <TableCell className="font-medium border-r">{row.tariffid}</TableCell>
                                <TableCell className="border-r">{row.description}</TableCell>
                                <TableCell className="border-r">{row.unitname}</TableCell>
                                <TableCell className="border-r">{row.forecast_year}</TableCell>
                                <TableCell className="text-right border-r">
                                  {row.forecast_advalorem != null
                                    ? `${(row.forecast_advalorem * 100).toFixed(2)}%`
                                    : '—'}
                                </TableCell>
                                <TableCell className="text-right border-r">
                                  {row.forecast_specificperunit != null
                                    ? `$${row.forecast_specificperunit.toFixed(2)}`
                                    : '—'}
                                </TableCell>
                                <TableCell>
                                  {row.created_at
                                    ? new Date(row.created_at).toLocaleDateString()
                                    : '—'}
                                </TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </div>

                {/* Pagination lives inside the white card too */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-4 px-4 md:px-6">
                  <div className="flex items-center gap-2 text-sm">
                    <span>Showing page {currentPage} of {totalPages}</span>
                    <span className="text-muted-foreground">|</span>
                    <Select value={String(pageSize)} onValueChange={(value) => {
                      setPageSize(Number(value));
                      setCurrentPage(1);
                    }}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="50">50 records</SelectItem>
                        <SelectItem value="100">100 records</SelectItem>
                        <SelectItem value="200">200 records</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>

                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }

                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-9"
                        >
                          {pageNum}
                        </Button>
                      );
                    })}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TooltipProvider>
      </div>
    </div>
  );
}
