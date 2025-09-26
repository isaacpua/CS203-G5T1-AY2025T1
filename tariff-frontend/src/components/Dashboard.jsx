import { useEffect, useState, useId, useCallback, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import axiosClient from "../api/axiosClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Search, Plus, Edit2, Trash2, X, MoreVertical, Eye, Download, RefreshCw, Check } from "lucide-react";
import { Grid, useClientRowDataSource } from "@1771technologies/lytenyte-core";
import "@1771technologies/lytenyte-core/grid.css";
import { Relogin } from "@/components/Relogin";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import Papa from 'papaparse';

function useDebounce(value, delayMs = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(handler);
  }, [value, delayMs]);
  return debouncedValue;
}

/* ---------------- cells ---------------- */
const TextCell = ({ row, column, grid }) => {
  const v = grid.api.columnField(column, row);
  return <div className="px-3 py-2 text-sm text-foreground">{v ?? "—"}</div>;
};

const DescriptionCell = ({ row, column, grid, onView }) => {
  const value = grid.api.columnField(column, row);
  const maxLength = 80; // Adjust this value to control truncation
  const isLong = value && value.length > maxLength;
  const displayText = isLong ? value.substring(0, maxLength) + "..." : value;
  
  const handleViewMore = () => {
    if (onView) {
      onView(row.data);
    }
  };
  
  return (
    <div className="flex items-center px-3 py-2 space-x-2">
      <span className="text-sm text-foreground flex-1">{displayText || "—"}</span>
      {isLong && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 flex-shrink-0 border border-gray-300 dark:border-gray-600 hover:bg-gray-100"
                onClick={handleViewMore}
              >
                <MoreVertical className="h-3 w-3" />
                <span className="sr-only">View full description</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Click to view full details</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
};

const TariffIdCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  return (
    <div className="flex items-center px-3 py-2">
      <Badge variant="secondary" className="font-mono text-xs">#{value}</Badge>
    </div>
  );
};

const CategoryCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  const categoryColors = {
    COMPOSITE: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:border-blue-800",
    SPECIFIC_PER_UNIT: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/50 dark:text-green-300 dark:border-green-800",
    AD_VALOREM: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/50 dark:text-purple-300 dark:border-purple-800",
    DEFAULT: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600",
  };
  const colorClass = categoryColors[value] || categoryColors.DEFAULT;
  return (
    <div className="flex items-center px-3 py-2">
      <Badge className={`${colorClass} border`}>{value?.replace(/_/g, " ")}</Badge>
    </div>
  );
};

const CountryCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  return (
    <div className="flex items-center px-3 py-2">
      <div className="flex items-center space-x-2">
        <div className="w-4 h-3 bg-gray-300 dark:bg-gray-700 rounded-sm flex-shrink-0" />
        <span className="text-sm font-medium">{value || "—"}</span>
      </div>
    </div>
  );
};

const MoneyCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  const n = Number(value);
  const show = Number.isFinite(n) && n !== 0;
  return (
    <div className="flex items-center justify-end px-3 py-2">
      <span className={`font-mono text-sm ${show ? "text-foreground" : "text-muted-foreground"}`}>
        {show ? `$${n.toFixed(2)}` : "—"}
      </span>
    </div>
  );
};

const ActionCell = ({ userRole, row, onEdit, onDelete, onView }) => (
  <div className="flex items-center justify-center px-3 py-2">
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <MoreVertical className="h-4 w-4" />
          <span className="sr-only">Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuItem onClick={() => onView(row.data)}><Eye className="mr-2 h-4 w-4" />View Details</DropdownMenuItem>
        {userRole === "admin" && (<DropdownMenuItem onClick={() => onEdit(row.data)}><Edit2 className="mr-2 h-4 w-4" />Edit</DropdownMenuItem>)}
        {userRole === "admin" && (<>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => onDelete(row.data)} className="text-red-600 focus:text-red-600 dark:text-red-500 dark:focus:text-red-400">
            <Trash2 className="mr-2 h-4 w-4" />Delete
          </DropdownMenuItem>
        </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
);

const SortableHeader = ({ column, grid }) => {
  const sort = grid.state.sortModel.useValue().find((c) => c.columnId === column.id);
  const isDescending = sort?.isDescending ?? false;

  const handleSort = () => {
    const current = grid.api.sortForColumn(column.id);
    if (current == null) {
      grid.state.sortModel.set([{ columnId: column.id, sort: { kind: "string" } }]);
      return;
    }
    if (!current.sort.isDescending) {
      grid.state.sortModel.set([{ ...current, sort: { ...current.sort, isDescending: true } }]);
    } else {
      grid.state.sortModel.set([]);
    }
  };

  return (
    <div
      className="flex items-center justify-between px-3 py-3 h-full w-full bg-muted/50 hover:bg-muted/80 cursor-pointer transition-colors border-b border-border font-semibold text-foreground text-sm"
      onClick={handleSort}
    >
      <span>{column.name}</span>
      {sort && <div className="ml-2">{!isDescending ? "↑" : "↓"}</div>}
    </div>
  );
};

const StaticHeader = ({ column }) => (
  <div className="flex items-center justify-center px-3 py-3 h-full w-full bg-muted/50 border-b border-border font-semibold text-foreground text-sm">
    <span>{column.name}</span>
  </div>
);

/* ---------------- grid wrapper ---------------- */
function TariffGrid({ userRole, data, onEdit, onDelete, onView }) {
  const columns = useMemo(
    () => [
      { id: "tariffid", name: "Tariff ID", width: 120, resizable: true, cellRenderer: TariffIdCell, headerRenderer: SortableHeader },
      { id: "category", name: "Category", width: 180, resizable: true, cellRenderer: CategoryCell, headerRenderer: SortableHeader },
      { id: "descriptionwcountry", name: "Description", width: 500, resizable: true, cellRenderer: (props) => <DescriptionCell {...props} onView={onView} />, headerRenderer: SortableHeader },
      { id: "partnerCountry", name: "Partner Country", width: 160, resizable: true, cellRenderer: CountryCell, headerRenderer: SortableHeader },
      { id: "reporterCountry", name: "Reporter Country", width: 160, resizable: true, cellRenderer: CountryCell, headerRenderer: SortableHeader },
      { id: "adValorem", name: "Ad Valorem", width: 120, resizable: true, cellRenderer: MoneyCell, headerRenderer: SortableHeader },
      { id: "specificPerUnit", name: "Specific/Unit", width: 120, resizable: true, cellRenderer: MoneyCell, headerRenderer: SortableHeader },
      { id: "actions", name: "Actions", width: 80, resizable: false, cellRenderer: (p) => <ActionCell {...p} userRole={userRole} onEdit={onEdit} onDelete={onDelete} onView={onView} />, headerRenderer: StaticHeader },
    ],
    [onEdit, onDelete, onView]
  );

  // hook required by the grid library (mounted only when we have data)
  const ds = useClientRowDataSource({ data });

  const grid = Grid.useLyteNyte({
    gridId: useId(),
    columns,
    rowDataSource: ds,
    rowHeight: 56,
    headerHeight: 52,
    rowSelection: { mode: "multiple", checkboxSelection: true },
    columnMarkerEnabled: true,
    editCellMode: "cell",
    editClickActivator: "double-click",
    columnBase: { editable: false },
  });

  const view = grid.view.useValue();

  return (
    <div className="border rounded-xl shadow-sm bg-card overflow-hidden" style={{ width: "100%", height: "520px" }}>
      <Grid.Root grid={grid}>
        <Grid.Viewport>
          <Grid.Header>
            {view.header.layout.map((row, i) => (
              <Grid.HeaderRow headerRowIndex={i} key={i}>
                {row.map((c) => (c.kind === "group" ? <Grid.HeaderGroupCell cell={c} key={c.idOccurrence} /> : <Grid.HeaderCell cell={c} key={c.column.id} />))}
              </Grid.HeaderRow>
            ))}
          </Grid.Header>
          <Grid.RowsContainer>
            <Grid.RowsCenter>
              {view.rows.center.map((row) =>
                row.kind === "full-width" ? (
                  <Grid.RowFullWidth row={row} key={row.id} />
                ) : (
                  <Grid.Row key={row.id} row={row} className="hover:bg-muted/50 transition-colors duration-150 text-foreground">
                    {row.cells.map((cell) => (
                      <Grid.Cell cell={cell} key={cell.id} />
                    ))}
                  </Grid.Row>
                )
              )}
            </Grid.RowsCenter>
          </Grid.RowsContainer>
        </Grid.Viewport>
      </Grid.Root>
    </div>
  );
}

/* ---------------- validation ---------------- */
const validateTariffForm = (form) => {
  const errors = {};
  if (!form.category || form.category.trim() === "") errors.category = "Category is required";
  if (!form.descriptionwcountry || form.descriptionwcountry.trim() === "") errors.descriptionwcountry = "Description is required";
  if (form.adValorem && isNaN(parseFloat(form.adValorem))) errors.adValorem = "Ad Valorem must be a valid number";
  if (form.specificPerUnit && isNaN(parseFloat(form.specificPerUnit))) errors.specificPerUnit = "Specific per unit must be a valid number";
  return errors;
};

/* ---------------- modals ---------------- */
const TariffModal = ({ isOpen, onClose, onSubmit, initialData, isEditing, isLoading, error }) => {
  const [form, setForm] = useState(initialData || {});
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (initialData) setForm(initialData);
    setErrors({});
  }, [initialData, isOpen]);

  const handleSubmit = () => {
    const validationErrors = validateTariffForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    onSubmit(form);
  };

  const hasChanges = JSON.stringify(form) !== JSON.stringify(initialData);

  const categories = ["COMPOSITE", "SPECIFIC_PER_UNIT", "AD_VALOREM", "FOOD_BEVERAGE", "MINERAL", "CHEMICAL", "PLASTIC", "TEXTILE", "WOOD", "PAPER"];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">{isEditing ? "Edit Tariff Entry" : "Create New Tariff Entry"}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-6 py-6">
          <div className="space-y-2">
            <Label htmlFor="category">Category <span className="text-red-500">*</span></Label>
            <Select value={form.category || ""} onValueChange={(value) => setForm((f) => ({ ...f, category: value }))}>
              <SelectTrigger className={errors.category ? "border-red-500" : ""}><SelectValue placeholder="Select category" /></SelectTrigger>
              <SelectContent>{categories.map((cat) => <SelectItem key={cat} value={cat}>{cat.replace(/_/g, " ")}</SelectItem>)}</SelectContent>
            </Select>
            {errors.category && <p className="text-sm text-red-500">{errors.category}</p>}
          </div>

          <div className="col-span-2 space-y-2">
            <Label htmlFor="descriptionwcountry">Description <span className="text-red-500">*</span></Label>
            <Input id="descriptionwcountry" value={form.descriptionwcountry || ""} onChange={(e) => setForm((f) => ({ ...f, descriptionwcountry: e.target.value }))} className={errors.descriptionwcountry ? "border-red-500" : ""} placeholder="e.g., Industrial Machinery" />
            {errors.descriptionwcountry && <p className="text-sm text-red-500">{errors.descriptionwcountry}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="partnerCountry">Partner Country <span className="text-red-500">*</span></Label>
            <Input id="partnerCountry" value={form.partnerCountry || ""} onChange={(e) => setForm((f) => ({ ...f, partnerCountry: e.target.value }))} className={errors.partnerCountry ? "border-red-500" : ""} placeholder="e.g., Singapore (Case Sensitive)" />
            {errors.partnerCountry && <p className="text-sm text-red-500">{errors.partnerCountry}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="reporterCountry">Reporter Country <span className="text-red-500">*</span></Label>
            <Input id="reporterCountry" value={form.reporterCountry || ""} onChange={(e) => setForm((f) => ({ ...f, reporterCountry: e.target.value }))} className={errors.reporterCountry ? "border-red-500" : ""} placeholder="e.g., China (Case Sensitive)" />
            {errors.reporterCountry && <p className="text-sm text-red-500">{errors.reporterCountry}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="adValorem">Ad Valorem Rate</Label>
            <Input id="adValorem" type="number" step="0.01" min="0" value={form.adValorem || ""} onChange={(e) => setForm((f) => ({ ...f, adValorem: e.target.value }))} className={errors.adValorem ? "border-red-500" : ""} placeholder="e.g., 5.5" />
            {errors.adValorem && <p className="text-sm text-red-500">{errors.adValorem}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="specificPerUnit">Specific per Unit</Label>
            <Input id="specificPerUnit" type="number" step="0.01" min="0" value={form.specificPerUnit || ""} onChange={(e) => setForm((f) => ({ ...f, specificPerUnit: e.target.value }))} className={errors.specificPerUnit ? "border-red-500" : ""} placeholder="e.g., 12.50" />
            {errors.specificPerUnit && <p className="text-sm text-red-500">{errors.specificPerUnit}</p>}
          </div>

          <div className="col-span-2 space-y-2">
            <Label htmlFor="unitname">Unit Name</Label>
            <Input id="unitname" value={form.unitname || ""} onChange={(e) => setForm((f) => ({ ...f, unitname: e.target.value }))} placeholder="e.g., kg" />
          </div>

        </div>

        {error && <div className="p-3 bg-red-50 border border-red-200 rounded-md"><p className="text-sm text-red-600">{error}</p></div>}

        <DialogFooter className="flex gap-3">
          <Button variant="outline" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading || (isEditing && !hasChanges)}>
            {isLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />{isEditing ? "Updating..." : "Creating..."}</>) : (<><Check className="mr-2 h-4 w-4" />{isEditing ? "Update" : "Create"}</>)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const ViewDetailsModal = ({ isOpen, onClose, data }) => {
  if (!data) return null;
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Badge variant="secondary" className="font-mono">#{data.tariffid}</Badge>
            <span>Tariff Details</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Category</Label>
              <div className="mt-1"><Badge className="bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:border-blue-800">{data.category?.replace(/_/g, " ")}</Badge></div>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Unit Name</Label>
              <p className="mt-1 text-sm">{data.unitname || "—"}</p>
            </div>
          </div>

          <div>
            <Label className="text-sm font-medium text-muted-foreground">Description</Label>
            <p className="mt-1 text-sm bg-gray-50 dark:bg-gray-800 p-3 rounded-md">{data.descriptionwcountry}</p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Partner Country</Label>
              <div className="mt-1 flex items-center space-x-2"><div className="w-4 h-3 bg-gray-200 dark:bg-gray-700 rounded-sm" /><span className="text-sm">{data.partnerCountry}</span></div>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Reporter Country</Label>
              <div className="mt-1 flex items-center space-x-2"><div className="w-4 h-3 bg-gray-200 dark:bg-gray-700 rounded-sm" /><span className="text-sm">{data.reporterCountry}</span></div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Ad Valorem Rate</Label>
              <p className="mt-1 text-lg font-mono text-foreground">{data.adValorem ? `$${parseFloat(data.adValorem).toFixed(2)}` : "—"}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Specific per Unit</Label>
              <p className="mt-1 text-lg font-mono text-foreground">{data.specificPerUnit ? `$${parseFloat(data.specificPerUnit).toFixed(2)}` : "—"}</p>
            </div>
          </div>
        </div>

        <DialogFooter><Button onClick={onClose}>Close</Button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/* ---------------- main ---------------- */
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
  const [showView, setShowView] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [showRelogin, setShowRelogin] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const debouncedQuery = useDebounce(query);

  const userRole = JSON.parse(localStorage.getItem("user")).role;

  // Reset page when filters change
  useEffect(() => { setPage(0); }, [debouncedQuery, mode]);

  const fetchTariffs = useCallback(async (showRefreshLoader = false) => {
    if (showRefreshLoader) setIsRefreshing(true); else setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({ page: String(page), size: String(pageSize) });
      const dQ = debouncedQuery.trim();
      if (dQ) {
        if (mode === "id") params.set("tariffid", dQ);
        if (mode === "desc") params.set("q", dQ);
      }
      const { data } = await axiosClient.get(`/dashboard/tariffs?${params.toString()}`);

      // Normalize fields so they always match our column IDs
      const mappedContent = (Array.isArray(data.content) ? data.content : []).map((row) => {
        const tariffid = row.tariffid ?? row.tariffId ?? row.id ?? "";
        return {
          id: tariffid,
          tariffid,
          category: row.category ?? "",
          descriptionwcountry: row.descriptionwcountry ?? row.descriptionWCountry ?? row.description ?? "",
          partnerCountry: row.partnerCountry ?? row.partnerCountry ?? "",
          reporterCountry: row.reporterCountry ?? row.reporterCountry ?? "",
          adValorem: row.adValorem ?? row.adValorem ?? "",
          specificPerUnit: row.specificPerUnit ?? row.specificPerUnit ?? "",
          unitname: row.unitname ?? row.unitName ?? "",
        };
      });

      setResults({
        content: mappedContent,
        totalPages: data.totalPages ?? 0,
        totalElements: data.totalElements ?? mappedContent.length,
      });

      if (showRefreshLoader && mappedContent.length > 0) {
        toast.success(`Refreshed ${mappedContent.length} tariff records`);
      }
    } catch (err) {
      if (err.response?.status === 401) { setShowRelogin(true); return; }
      setError("Failed to fetch tariffs. Please try again.");
      toast.error("Failed to fetch tariff data");
      console.error(err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [page, pageSize, debouncedQuery, mode]);

  useEffect(() => { fetchTariffs(); }, [fetchTariffs]);

  const handleEdit = (row) => { setSelectedRow(row); setShowEdit(true); };
  const handleDelete = (row) => { setSelectedRow(row); setShowDelete(true); };
  const handleView = (row) => { setSelectedRow(row); setShowView(true); };
  const handleCreate = () => { setSelectedRow(null); setShowCreate(true); };
  const handleRefresh = () => { fetchTariffs(true); };
  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const { data } = await axiosClient.get("/dashboard/tariffs?size=-1");

      // Define the fields you want to export and their display names
      const fields = [
        { key: 'tariffId', label: 'Tariff ID' },
        { key: 'descriptionwcountry', label: 'Description' },
        { key: 'partnerCountry', label: 'Partner Country' },
        { key: 'reporterCountry', label: 'Reporter Country' },
        { key: 'unitname', label: 'Unit Name' },
        { key: 'category', label: 'Category' },
        { key: 'adValorem', label: 'Ad Valorem' },
        { key: 'specificPerUnit', label: 'Specific Per Unit' }
      ];

      // Transform data to ensure consistent field names
      const transformedData = data.tariffs.map(item => {
        const transformed = {};
        fields.forEach(field => {
          transformed[field.label] = item[field.key] || '';
        });
        return transformed;
      });

      // Convert to CSV using Papaparse
      const csv = Papa.unparse(transformedData, {
        header: true,
        skipEmptyLines: true
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = `tariffs_${new Date().toISOString()}.csv`;
      a.click();

      window.URL.revokeObjectURL(url);
      toast.success(`Exported ${data.tariffs.length} tariff records`);
    } catch (err) {
      if (err.response?.status === 401) {
        setShowRelogin(true);
        return;
      }
      console.error('Download failed:', err);
      toast.error('Failed to export data');
    } finally {
      setIsDownloading(false);
    }
  };

  const closeDialogs = () => {
    setShowCreate(false); setShowEdit(false); setShowDelete(false); setShowView(false);
    setSelectedRow(null); setActionError("");
  };

  const onSaveChanges = async (formData) => {
    setActionLoading(true); setActionError("");
    console.log("Form data to submit:", formData);
    delete formData.tariffid
    try {
      if (showEdit) {
        console.log("Updating tariff with ID:", selectedRow.id, "and data:", formData);
        await axiosClient.patch(`/dashboard/tariffs/${selectedRow.id}`, formData);
        toast.success("Tariff updated successfully");
      } else {
        console.log("Creating tariff with data:", formData);
        await axiosClient.post("/dashboard/tariffs", formData);
        toast.success("Tariff created successfully");
      }
      closeDialogs();
      fetchTariffs();
    } catch (err) {
      if (err.response?.status === 401) { setShowRelogin(true); return; }
      const errorMsg = err.response?.data?.message || "Failed to save changes.";
      setActionError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  const onDeleteConfirm = async () => {
    setActionLoading(true); setActionError("");
    try {
      await axiosClient.delete(`/dashboard/tariffs/${selectedRow.id}`);
      toast.success("Tariff deleted successfully");
      closeDialogs();
      fetchTariffs();
    } catch (err) {
      if (err.response?.status === 401) { setShowRelogin(true); return; }
      const errorMsg = err.response?.data?.message || "Failed to delete tariff.";
      setActionError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <TooltipProvider>
      {showRelogin && <Relogin />}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-4 md:p-6">
          <div className="flex flex-col space-y-4 md:flex-row md:justify-between md:items-center md:space-y-0">
            <div className="space-y-1">
              <CardTitle className="text-xl md:text-2xl font-bold text-foreground">Tariff Management</CardTitle>
              <CardDescription className="text-sm md:text-base text-muted-foreground">Manage and explore tariff data with advanced filtering and editing capabilities</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
                    <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Refresh data</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" onClick={handleDownload} disabled={isDownloading}>
                    <Download className={`h-4 w-4 ${isDownloading ? "animate-spin" : ""}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export data</TooltipContent>
              </Tooltip>
              {userRole === "admin" && (
                <Button onClick={handleCreate} size="sm" className="text-sm">
                  <Plus className="mr-1 md:mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Create Tariff</span>
                  <span className="sm:hidden">Create</span>
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 md:p-6">
          {/* Search Controls */}
          <div className="flex flex-col md:flex-row md:items-end gap-4 mb-6 p-4 bg-muted/30 rounded-xl border">
            <div className="w-full md:flex-1">
              <Label className="text-sm font-medium text-foreground">Search Method</Label>
              <Select value={mode} onValueChange={setMode}>
                <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="id"><div className="flex items-center"><Badge variant="outline" className="mr-2 text-xs">ID</Badge>Tariff ID</div></SelectItem>
                  <SelectItem value="desc"><div className="flex items-center"><Search className="mr-2 h-3 w-3" />Description</div></SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-full md:flex-[3]">
              <Label className="text-sm font-medium text-foreground">{mode === "id" ? "Enter Tariff ID" : "Search Description"}</Label>
              <div className="relative mt-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input value={query} onChange={(e) => setQuery(e.target.value)} className="pl-10 pr-4" placeholder={mode === "id" ? "e.g., 12345" : "e.g., electronics, beverages..."} />
                {query && (
                  <Button variant="ghost" size="sm" className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0" onClick={() => setQuery("")}>
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-2">
              <Badge variant="secondary" className="text-xs">{results ? `${results.totalElements ?? results.content.length} results` : "Loading..."}</Badge>
              {debouncedQuery && <Badge variant="outline" className="text-xs">Filtered</Badge>}
            </div>
          </div>

          {/* Content area */}
          {error ? (
            <div className="flex flex-col items-center justify-center p-12 h-[520px] bg-destructive/10 border border-destructive/20 rounded-xl">
              <div className="text-center">
                <div className="w-16 h-16 bg-destructive/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="h-8 w-8 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Error Loading Data</h3>
                <p className="text-muted-foreground mb-4">{error}</p>
                <Button onClick={() => fetchTariffs()} variant="outline"><RefreshCw className="mr-2 h-4 w-4" />Try Again</Button>
              </div>
            </div>
          ) : loading ? (
            <div className="border rounded-xl bg-card h-[520px] grid place-items-center">
              <div className="flex items-center space-x-3">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="text-muted-foreground">Loading tariff data…</span>
              </div>
            </div>
          ) : results && results.content.length > 0 ? (
            <TariffGrid userRole={userRole} data={results.content} onEdit={handleEdit} onDelete={handleDelete} onView={handleView} />
          ) : (
            <div className="flex flex-col items-center justify-center p-12 h-[520px] bg-muted/30 border rounded-xl">
              <div className="text-center">
                <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No Results Found</h3>
                <p className="text-muted-foreground mb-4">{query ? `No tariffs match "${query}"` : "No tariff data available"}</p>
                {query && <Button onClick={() => setQuery("")} variant="outline">Clear Search</Button>}
              </div>
            </div>
          )}

          {/* Pagination */}
          {results && results.totalPages > 1 && (
            <div className="flex justify-between items-center pt-6 border-t">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">Showing page {page + 1} of {results.totalPages}</span>
                <Badge variant="outline" className="text-xs">{results.content.length} records</Badge>
              </div>

              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" disabled={page <= 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, results.totalPages) }, (_, i) => {
                    const pageNum = i + Math.max(0, page - 2);
                    if (pageNum >= results.totalPages) return null;
                    return (
                      <Button key={pageNum} variant={pageNum === page ? "default" : "outline"} size="sm" className="w-8 h-8 p-0" onClick={() => setPage(pageNum)}>
                        {pageNum + 1}
                      </Button>
                    );
                  })}
                </div>
                <Button variant="outline" size="sm" disabled={page + 1 >= results.totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      <TariffModal
        isOpen={showCreate}
        onClose={closeDialogs}
        onSubmit={onSaveChanges}
        initialData={{ category: "", descriptionwcountry: "", partnerCountry: "", reporterCountry: "", adValorem: "", specificPerUnit: "", unitname: "" }}
        isEditing={false}
        isLoading={actionLoading}
        error={actionError}
      />
      <TariffModal isOpen={showEdit} onClose={closeDialogs} onSubmit={onSaveChanges} initialData={selectedRow} isEditing={true} isLoading={actionLoading} error={actionError} />
      <ViewDetailsModal isOpen={showView} onClose={closeDialogs} data={selectedRow} />

      <Dialog open={showDelete} onOpenChange={closeDialogs}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-red-100 dark:bg-red-900/40 rounded-full flex items-center justify-center"><Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" /></div>
              <span>Delete Tariff</span>
            </DialogTitle>
          </DialogHeader>

          <div className="py-4">
            <p className="text-muted-foreground">Are you sure you want to delete this tariff entry? This action cannot be undone.</p>
            {selectedRow && (
              <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary" className="font-mono">#{selectedRow.tariffid}</Badge>
                  <span className="text-sm text-muted-foreground">{selectedRow.descriptionwcountry}</span>
                </div>
              </div>
            )}
          </div>

          {actionError && <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-md"><p className="text-sm text-red-600 dark:text-red-400">{actionError}</p></div>}

          <DialogFooter className="flex gap-3">
            <Button variant="outline" onClick={closeDialogs} disabled={actionLoading}>Cancel</Button>
            <Button variant="destructive" onClick={onDeleteConfirm} disabled={actionLoading}>
              {actionLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />Deleting...</>) : (<><Trash2 className="mr-2 h-4 w-4" />Delete</>)}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
};