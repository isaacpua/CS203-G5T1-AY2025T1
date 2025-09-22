import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
import { Loader2, Search } from "lucide-react";
import { Grid, useClientRowDataSource } from "@1771technologies/lytenyte-core";
import "@1771technologies/lytenyte-core/grid.css";
import { useId } from "react";

// A debounced hook to prevent API calls on every keystroke
function useDebounce(value, delayMs = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);
    return () => {
      clearTimeout(handler);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

function isIntegerLike(str) {
    return /^\d+$/.test(str.trim());
}

export default function Dashboard() {
  const [mode, setMode] = useState("desc"); // "id" | "hts8" | "desc"
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageInput, setPageInput] = useState("1");
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState({
    content: [],
    totalPages: 0,
    number: 0,
  });

  const debouncedQuery = useDebounce(query);

  // LyteNyte Grid setup (hooks must be top-level)
  const columns = [
    { id: "tariffid", name: "Tariff ID" },
    { id: "name", name: "Name" },
    { id: "category", name: "Category" },
    { id: "descriptionwcountry", name: "Description" },
    { id: "partnercountry", name: "Partner Country" },
    { id: "reportercountry", name: "Reporter Country" },
    { id: "advalorem", name: "Ad Valorem" },
    { id: "specificperunit", name: "Specific/Unit" },
    { id: "unitid", name: "Unit ID" },
  ];
  const ds = useClientRowDataSource({
    data: results.content,
  });
  const grid = Grid.useLyteNyte({
    gridId: useId(),
    columns,
    rowDataSource: ds,
  });
  const view = grid.view.useValue();

  useEffect(() => {
    const fetchTariffs = async () => {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          page: page,
          size: pageSize,
        });
        const dQ = debouncedQuery.trim();
        if (dQ) {
            if ((mode === "id" || mode === "hts8") && !isIntegerLike(dQ)) {
                setError("Please input an integer.");
                setResults({ content: [], totalPages: 0, number: 0 });
                setLoading(false);
                return;
            }
            if (mode === "id") params.set("id", dQ);
            if (mode === "hts8") params.set("hts8", dQ);
            if (mode === "desc") params.set("q", dQ);
        }

        const { data } = await axiosClient.get(
          `/tariffs/search?${params.toString()}`
        );
        // Map tariff_new columns for grid
        setResults({
          ...data,
          content: Array.isArray(data.content)
            ? data.content.map((row) => ({
                tariffid: row.tariffid,
                name: row.name,
                category: row.category,
                descriptionwcountry: row.descriptionwcountry,
                partnercountry: row.partnercountry,
                reportercountry: row.reportercountry,
                advalorem: row.advalorem ?? row.ad_valorem,
                specificperunit: row.specificperunit ?? row.specific_per_unit,
                unitid: row.unitid,
                id: row.id,
              }))
            : [],
        });
        setPageInput(String(data.number + 1));
      } catch (err) {
        setError("Failed to fetch tariffs. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTariffs();
  }, [debouncedQuery, page, pageSize, mode]);

  // Reset page to 0 when query or mode changes
  useEffect(() => {
    setPage(0);
  }, [debouncedQuery, mode]);
  
  const handlePageInputChange = (e) => {
    setPageInput(e.target.value);
  };

  const handlePageJump = () => {
    const pageNum = Number(pageInput);
    if (
      !isNaN(pageNum) &&
      pageNum > 0 &&
      pageNum <= results.totalPages
    ) {
      setPage(pageNum - 1);
    } else {
      setPageInput(String(page + 1)); // Reset to current page if invalid
    }
  };


  return (
    <Card>
      <CardHeader>
        <CardTitle>Tariff Dashboard</CardTitle>
        <CardDescription>
          Displaying entries from the database. Use the search bar to filter.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4">
            <div className="grid grid-cols-3 gap-4 w-full">
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
                    <Label>{mode === 'id' ? 'ID' : mode === 'hts8' ? 'HTS8 Code' : 'Brief Description'}</Label>
                    <div className="relative flex-grow">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                        placeholder={mode === 'desc' ? 'e.g., sunglasses, lenses...' : 'Enter number'}
                        className="pl-10"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        />
                    </div>
                </div>
            </div>
        </div>

        {loading && (
          <div className="flex justify-center items-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

  <div className="border rounded-md lng-grid light" style={{ width: "100%", height: "400px" }}>
          <Grid.Root grid={grid}>
            <Grid.Viewport>
              <Grid.Header>
                {view.header.layout.map((row, i) => (
                  <Grid.HeaderRow headerRowIndex={i} key={i}>
                    {row.map((c) => {
                      if (c.kind === "group") {
                        return (
                          <Grid.HeaderGroupCell cell={c} key={c.idOccurrence} />
                        );
                      }
                      return <Grid.HeaderCell cell={c} key={c.column.id} />;
                    })}
                  </Grid.HeaderRow>
                ))}
              </Grid.Header>
              <Grid.RowsContainer>
                <Grid.RowsCenter>
                  {view.rows.center.map((row) => {
                    if (row.kind === "full-width") {
                      return <Grid.RowFullWidth row={row} key={row.id} />;
                    }
                    return (
                      <Grid.Row key={row.id} row={row} accepted={["row"]}>
                        {row.cells.map((cell) => (
                          <Grid.Cell cell={cell} key={cell.id} />
                        ))}
                      </Grid.Row>
                    );
                  })}
                </Grid.RowsCenter>
              </Grid.RowsContainer>
            </Grid.Viewport>
          </Grid.Root>
          {results.content.length === 0 && !loading && (
            <div className="text-center p-12">No results found.</div>
          )}
        </div>

        {/* Pagination */}
        {results.totalPages > 1 && (
          <div className="flex justify-between items-center pt-4">
            <Button
              variant="outline"
              disabled={page <= 0 || loading}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                Page
                <Input
                  type="number"
                  className="h-8 w-16 text-center"
                  value={pageInput}
                  onChange={handlePageInputChange}
                  onKeyDown={(e) => e.key === 'Enter' && handlePageJump()}
                  onBlur={handlePageJump}
                  min="1"
                  max={results.totalPages}
                />
                of {results.totalPages}
            </div>
            <Button
              variant="outline"
              disabled={results.number + 1 >= results.totalPages || loading}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}