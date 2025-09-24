import { useEffect, useState, useId, useCallback, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Search } from "lucide-react";
import { Grid, useClientRowDataSource } from "@1771technologies/lytenyte-core";
import "@1771technologies/lytenyte-core/grid.css";

function useDebounce(value, delayMs = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(handler);
  }, [value, delayMs]);
  return debouncedValue;
}

// Child component to ensure grid is only initialized with data
function TariffGrid({ data, onEdit, onDelete }) {
  const columns = useMemo(() => [
    { id: "tariffid", name: "Tariff ID", resizable: true },
    { id: "name", name: "Name", resizable: true },
    { id: "category", name: "Category", resizable: true },
    { id: "descriptionwcountry", name: "Description", resizable: true },
    { id: "partnercountry", name: "Partner Country", resizable: true },
    { id: "reportercountry", name: "Reporter Country", resizable: true },
    { id: "unitname", name: "Unit Name", resizable: true },
    {
      id: "actions", name: "Actions",
      render: (row) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => onEdit(row)}>Edit</Button>
          <Button size="sm" variant="destructive" onClick={() => onDelete(row)}>Delete</Button>
        </div>
      ),
    }
  ], [onEdit, onDelete]);

  const ds = useClientRowDataSource({ data });

  const grid = Grid.useLyteNyte({
    gridId: useId(), columns, rowDataSource: ds, theme: "dark",
    rowHeight: 44, headerHeight: 48,
    style: { background: "var(--background)", color: "var(--foreground)", borderRadius: "0.75rem" },
  });
  const view = grid.view.useValue();

  return (
    <div className="border rounded-xl shadow-lg bg-card" style={{ width: "100%", height: "480px", overflow: "auto" }}>
      <Grid.Root grid={grid}>
        <Grid.Viewport>
          <Grid.Header>
            {view.header.layout.map((row, i) => (<Grid.HeaderRow headerRowIndex={i} key={i}>{row.map((c) => <Grid.HeaderCell cell={c} key={c.column.id} />)}</Grid.HeaderRow>))}
          </Grid.Header>
          <Grid.RowsContainer>
            <Grid.RowsCenter>
              {view.rows.center.map((row) => (<Grid.Row key={row.id} row={row}>{row.cells.map((cell) => <Grid.Cell cell={cell} key={cell.id} />)}</Grid.Row>))}
            </Grid.RowsCenter>
          </Grid.RowsContainer>
        </Grid.Viewport>
      </Grid.Root>
    </div>
  );
}

// Main Dashboard component for fetching and state management
export default function Dashboard() {
  const [mode, setMode] = useState("desc");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  const [form, setForm] = useState({});
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const debouncedQuery = useDebounce(query);

  const fetchTariffs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ page: String(page), size: String(pageSize) });
      const dQ = debouncedQuery.trim();
      if (dQ) {
        if (mode === "id") params.set("id", dQ);
        if (mode === "desc") params.set("q", dQ);
      }
      const { data } = await axiosClient.get(`/dashboard/tariffs?${params.toString()}`);
      
      const mappedContent = Array.isArray(data.content)
        ? data.content.map(row => ({
            id: row.id,
            tariffid: row.tariffid ?? "", name: row.name ?? "", category: row.category ?? "",
            descriptionwcountry: row.descriptionwcountry ?? "", partnercountry: row.partnercountry ?? "",
            reportercountry: row.reportercountry ?? "", advalorem: row.advalorem ?? "",
            specificperunit: row.specificperunit ?? "", unitname: row.unitname ?? ""
          }))
        : [];
      setResults({ content: mappedContent, totalPages: data.totalPages ?? 0 });
    } catch (err) {
      setError("Failed to fetch tariffs.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, debouncedQuery, mode]);

  useEffect(() => {
    fetchTariffs();
  }, [fetchTariffs]);

  const handleEdit = (row) => { setForm(row); setSelectedRow(row); setShowEdit(true); };
  const handleDelete = (row) => { setSelectedRow(row); setShowDelete(true); };

  const handleCreate = () => {
    setForm({ tariffid: "", name: "", category: "", descriptionwcountry: "", partnercountry: "", reportercountry: "", advalorem: "", specificperunit: "", unitname: "" });
    setShowCreate(true);
  };

  const closeDialogs = () => {
    setShowCreate(false);
    setShowEdit(false);
    setShowDelete(false);
    setActionError("");
  };

  const onSaveChanges = async () => {
    setActionLoading(true);
    setActionError("");
    try {
        if (showEdit) {
            await axiosClient.patch(`/dashboard/tariffs/${selectedRow.id}`, form);
        } else {
            await axiosClient.post("/dashboard/tariffs", form);
        }
        closeDialogs();
        fetchTariffs();
    } catch (err) {
        setActionError("Failed to save changes.");
    } finally {
        setActionLoading(false);
    }
  };

  const onDeleteConfirm = async () => {
    setActionLoading(true);
    setActionError("");
    try {
        await axiosClient.delete(`/dashboard/tariffs/${selectedRow.id}`);
        closeDialogs();
        fetchTariffs();
    } catch (err) {
        setActionError("Failed to delete tariff.");
    } finally {
        setActionLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Tariff Dashboard</CardTitle>
            <CardDescription>Displaying entries from the database.</CardDescription>
          </div>
          <Button onClick={handleCreate}>+ Create Tariff</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search controls */}
        <div className="flex gap-4">
            <div className="flex-1">
              <Label>Search by</Label>
              <Select value={mode} onValueChange={setMode}><SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="id">ID</SelectItem><SelectItem value="desc">Description</SelectItem></SelectContent>
              </Select>
            </div>
            <div className="flex-[2]">
              <Label>{mode === 'id' ? 'ID' : 'Brief Description'}</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input value={query} onChange={(e) => setQuery(e.target.value)} className="pl-10" />
              </div>
            </div>
        </div>
        
        {/* Conditional Rendering of Grid */}
        {loading ? (
          <div className="flex justify-center items-center p-8 h-[480px]">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="text-center text-destructive p-4 h-[480px]">{error}</div>
        ) : results && results.content.length > 0 ? (
          <TariffGrid data={results.content} onEdit={handleEdit} onDelete={handleDelete} />
        ) : (
          <div className="text-center p-12 border rounded-lg h-[480px] flex items-center justify-center">No results found.</div>
        )}

        {/* Pagination */}
        {results && results.totalPages > 1 && (
          <div className="flex justify-between items-center pt-4">
            <Button variant="outline" disabled={page <= 0} onClick={() => setPage(p => p - 1)}>Previous</Button>
            <span>Page {page + 1} of {results.totalPages}</span>
            <Button variant="outline" disabled={page + 1 >= results.totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
          </div>
        )}

        {/* CRUD Modals */}
        <Dialog open={showCreate || showEdit} onOpenChange={closeDialogs}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{showEdit ? "Edit Tariff" : "Create Tariff"}</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    {Object.keys(form).filter(key => key !== 'id').map((key) => (
                        <div key={key} className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor={key} className="text-right capitalize">{key}</Label>
                            <Input id={key} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} className="col-span-3" />
                        </div>
                    ))}
                </div>
                {actionError && <p className="text-sm text-destructive">{actionError}</p>}
                <DialogFooter>
                    <Button variant="outline" onClick={closeDialogs}>Cancel</Button>
                    <Button onClick={onSaveChanges} disabled={actionLoading}>
                        {actionLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Save changes"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>

        <Dialog open={showDelete} onOpenChange={closeDialogs}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Delete Tariff</DialogTitle>
                    <CardDescription>Are you sure you want to delete tariff ID: {selectedRow?.tariffid}?</CardDescription>
                </DialogHeader>
                {actionError && <p className="text-sm text-destructive">{actionError}</p>}
                <DialogFooter>
                    <Button variant="outline" onClick={closeDialogs}>Cancel</Button>
                    <Button variant="destructive" onClick={onDeleteConfirm} disabled={actionLoading}>
                        {actionLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Delete"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
        
      </CardContent>
    </Card>
  );
}