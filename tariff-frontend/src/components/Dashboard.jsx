import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
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
  // CRUD modal state
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  const [form, setForm] = useState({
    tariffid: "",
    name: "",
    category: "",
    descriptionwcountry: "",
    partnercountry: "",
    reportercountry: "",
    advalorem: "",
    specificperunit: "",
    unitid: ""
  });
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

  const debouncedQuery = useDebounce(query);

  // LyteNyte Grid setup (hooks must be top-level)
  const columns = [
    { id: "tariffid", name: "Tariff ID", resizable: true, reorderable: true, filterable: true },
    { id: "name", name: "Name", resizable: true, reorderable: true, filterable: true },
    { id: "category", name: "Category", resizable: true, reorderable: true, filterable: true },
    { id: "descriptionwcountry", name: "Description", resizable: true, reorderable: true, filterable: true },
    { id: "partnercountry", name: "Partner Country", resizable: true, reorderable: true, filterable: true },
    { id: "reportercountry", name: "Reporter Country", resizable: true, reorderable: true, filterable: true },
    { id: "advalorem", name: "Ad Valorem", resizable: true, reorderable: true, filterable: true },
    { id: "specificperunit", name: "Specific/Unit", resizable: true, reorderable: true, filterable: true },
    { id: "unitid", name: "Unit ID", resizable: true, reorderable: true, filterable: true },
    {
      id: "actions",
      name: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => { setSelectedRow(row); setForm(row); setShowEdit(true); }}>Edit</Button>
          <Button size="sm" variant="destructive" onClick={() => { setSelectedRow(row); setShowDelete(true); }}>Delete</Button>
        </div>
      ),
      resizable: false,
      reorderable: false,
      filterable: false
    }
  ];
  const ds = useClientRowDataSource({
    data: results.content,
  });
  const grid = Grid.useLyteNyte({
    gridId: useId(),
    columns,
    rowDataSource: ds,
    enableColumnResizing: true,
    enableColumnReordering: true,
    enableFiltering: true,
    enableGrouping: true,
    enableSorting: true,
    enableColumnPinning: true,
    enableColumnVisibility: true,
    enableColumnAutosizing: true,
    enableRowPinning: true,
    enableRowGrouping: true,
    enableRowSorting: true,
    enableRowPagination: true,
    enableRowDragging: true,
    enableCellEditing: true,
    enableExport: true,
    theme: "dark",
    fontFamily: "'Inter', 'Segoe UI', 'Arial', sans-serif",
    rowHeight: 44,
    headerHeight: 48,
    style: {
      background: "var(--background)",
      color: "var(--foreground)",
      borderRadius: "0.75rem",
      fontSize: "1rem"
    }
  });
  const view = grid.view.useValue();

  // Grid state atoms (safe checks)
  const selectedRows = grid.state.rowSelectedIds?.useValue?.() ?? [];
  const columnOrder = grid.state.columnOrder?.useValue?.() ?? columns.map(c => c.id);
  const filters = grid.state.filters?.useValue?.() ?? {};
  const pinnedColumns = grid.state.columnPinnedIds?.useValue?.() ?? [];
  const groupedColumns = grid.state.columnGroupIds?.useValue?.() ?? [];
  const sorting = grid.state.sorting?.useValue?.() ?? [];
  const pagination = grid.state.pagination?.useValue?.() ?? { page: 0, pageSize: 50 };

  // Example: Watch for selection changes
  useEffect(() => {
    const remove = grid.state.rowSelectedIds.watch(() => {
      // You could trigger analytics, chart updates, etc.
      // console.log("Selected rows changed:", grid.state.rowSelectedIds.get());
    });
    return remove;
  }, [grid.state.rowSelectedIds]);

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
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Tariff Dashboard</CardTitle>
            <CardDescription>
              Displaying entries from the database. Use the search bar to filter.
            </CardDescription>
          </div>
          <Button onClick={() => { setForm({ tariffid: "", name: "", category: "", descriptionwcountry: "", partnercountry: "", reportercountry: "", advalorem: "", specificperunit: "", unitid: "" }); setShowCreate(true); }}>+ Create Tariff</Button>
        </div>
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

        {/* Essential grid actions only */}
        <div className="my-4 flex gap-2">
          {grid.export?.csv && (
            <Button size="sm" variant="outline" onClick={() => grid.export.csv()}>Export CSV</Button>
          )}
          {grid.export?.excel && (
            <Button size="sm" variant="outline" onClick={() => grid.export.excel()}>Export Excel</Button>
          )}
          <Button size="sm" variant="outline" onClick={() => grid.state.rowSelectedIds?.set?.([])}>Clear Selection</Button>
        </div>

        {loading && (
          <div className="flex justify-center items-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}
        {error && (
          <div className="text-center text-destructive p-4">{error}</div>
        )}

        <div className="border rounded-xl shadow-lg bg-card" style={{ width: "100%", height: "480px", overflow: "hidden" }}>
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
      {/* Create Modal */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Tariff</DialogTitle>
          </DialogHeader>
          {/* Form fields */}
          {Object.keys(form).map((key) => (
            <div key={key} className="mb-2">
              <Label>{key}</Label>
              <Input value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
            </div>
          ))}
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
          <DialogFooter>
            <Button disabled={actionLoading} onClick={async () => {
              setActionLoading(true);
              setActionError("");
              try {
                await axiosClient.post("/tariffs", form);
                setShowCreate(false);
                setForm({ tariffid: "", name: "", category: "", descriptionwcountry: "", partnercountry: "", reportercountry: "", advalorem: "", specificperunit: "", unitid: "" });
                // Refresh grid
                setPage(0);
              } catch (err) {
                setActionError("Failed to create tariff.");
              } finally {
                setActionLoading(false);
              }
            }}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={showEdit} onOpenChange={setShowEdit}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Tariff</DialogTitle>
          </DialogHeader>
          {Object.keys(form).map((key) => (
            <div key={key} className="mb-2">
              <Label>{key}</Label>
              <Input value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />
            </div>
          ))}
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
          <DialogFooter>
            <Button disabled={actionLoading} onClick={async () => {
              setActionLoading(true);
              setActionError("");
              try {
                await axiosClient.put(`/tariffs/${form.id}`, form);
                setShowEdit(false);
                setSelectedRow(null);
                // Refresh grid
                setPage(0);
              } catch (err) {
                setActionError("Failed to update tariff.");
              } finally {
                setActionLoading(false);
              }
            }}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Modal */}
      <Dialog open={showDelete} onOpenChange={setShowDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Tariff</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete tariff <b>{selectedRow?.tariffid}</b>?</p>
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
          <DialogFooter>
            <Button variant="destructive" disabled={actionLoading} onClick={async () => {
              setActionLoading(true);
              setActionError("");
              try {
                await axiosClient.delete(`/tariffs/${selectedRow.id}`);
                setShowDelete(false);
                setSelectedRow(null);
                // Refresh grid
                setPage(0);
              } catch (err) {
                setActionError("Failed to delete tariff.");
              } finally {
                setActionLoading(false);
              }
            }}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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