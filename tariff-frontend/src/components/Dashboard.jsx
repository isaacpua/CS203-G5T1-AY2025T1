import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2, Search } from "lucide-react";

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

export default function Dashboard() {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState({ content: [], totalPages: 0, number: 0 });

  const debouncedQuery = useDebounce(query);

  useEffect(() => {
    const fetchTariffs = async () => {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams({
          page: page,
          size: pageSize,
        });
        // Only add the 'q' parameter if the user has typed something
        if (debouncedQuery.trim()) {
          params.set("q", debouncedQuery.trim());
        }

        const { data } = await axiosClient.get(`/tariffs/search?${params.toString()}`);
        setResults(data);
      } catch (err) {
        setError("Failed to fetch tariffs. Please try again.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTariffs();
  }, [debouncedQuery, page, pageSize]);
  
  // Reset page to 0 when query changes
  useEffect(() => {
    setPage(0);
  }, [debouncedQuery]);


  return (
    <Card>
      <CardHeader>
        <CardTitle>Tariff Dashboard</CardTitle>
        <CardDescription>
          Displaying entries from the database. Use the search bar to filter by description.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4">
          <div className="relative flex-grow">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search by tariff description..."
              className="pl-10"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <Button variant="outline" disabled>Filters</Button>
        </div>

        {loading && (
          <div className="flex justify-center items-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        <div className="border rounded-md">
            <div className="grid grid-cols-[auto_auto_1fr_1fr_auto] p-4 font-bold border-b gap-4">
                <div className="w-16">ID</div>
                <div className="w-24">HTS8</div>
                <div>Description</div>
                <div>MFN Rate</div>
                <div>Rate Type</div>
            </div>
            {results.content.length > 0 ? (
            results.content.map((tariff) => (
                <div key={tariff.id} className="grid grid-cols-[auto_auto_1fr_1fr_auto] p-4 border-b gap-4 items-center">
                    <div className="font-mono text-muted-foreground w-16">{tariff.id}</div>
                    <div className="font-mono w-24">{tariff.hts8}</div>
                    <div>{tariff.briefDescription}</div>
                    <div className="font-mono">{tariff.mfnTextRate}</div>
                    <div>
                        <span className={`px-2 py-1 text-xs rounded-full whitespace-nowrap ${tariff.isFree ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'}`}>
                        {tariff.overallKind}
                        </span>
                    </div>
                </div>
            ))
            ) : (
            <div className="text-center p-12">
                {!loading && "No results found."}
            </div>
            )}
        </div>
        
        {/* Pagination */}
        {results.totalPages > 1 && (
           <div className="flex justify-between items-center pt-4">
            <Button variant="outline" disabled={page <= 0 || loading} onClick={() => setPage(p => p - 1)}>
              Previous
            </Button>
            <div className="text-sm text-muted-foreground">
              Page {results.number + 1} of {results.totalPages}
            </div>
            <Button
              variant="outline"
              disabled={(results.number + 1 >= results.totalPages) || loading}
              onClick={() => setPage(p => p + 1)}
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