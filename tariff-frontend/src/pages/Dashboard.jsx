import { useEffect, useState, useId, useCallback, useMemo, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { createTariff, deleteTariff, getDashboardData, updateTariff } from "../api/axiosClient";
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
import CountrySelector from "@/components/CountrySelector";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

function useDebounce(value, delayMs = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delayMs);
    return () => clearTimeout(handler);
  }, [value, delayMs]);
  return debouncedValue;
}

function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia(query);
    const handler = (event) => setMatches(event.matches);
    setMatches(mediaQuery.matches);
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", handler);
      return () => mediaQuery.removeEventListener("change", handler);
    }
    mediaQuery.addListener(handler);
    return () => mediaQuery.removeListener(handler);
  }, [query]);

  return matches;
}

/* ---------------- cells ---------------- */
const TextCell = ({ row, column, grid }) => {
  const v = grid.api.columnField(column, row);
  return <div className="px-3 py-2 text-sm text-foreground">{v ?? "—"}</div>;
};

const DescriptionCell = ({ row, column, grid, onView }) => {
  const fullText = grid.api.columnField(column, row) ?? "";
  const textRef = useRef(null);
  const [canExpand, setCanExpand] = useState(false);

  const collapsedStyle = {
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "clip",
    WebkitMaskImage: canExpand ? "linear-gradient(90deg, #000 75%, rgba(0,0,0,0))" : undefined,
    maskImage: canExpand ? "linear-gradient(90deg, #000 75%, rgba(0,0,0,0))" : undefined,
  };

  useEffect(() => {
    const el = textRef.current;
    if (!el) return;

    const updateOverflow = () => {
      const isOverflowing = el.scrollWidth - el.clientWidth > 1;
      setCanExpand(isOverflowing);
    };

    updateOverflow();

    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(updateOverflow);
      observer.observe(el);
      return () => observer.disconnect();
    }

    if (typeof window !== "undefined") {
      window.addEventListener("resize", updateOverflow);
      return () => window.removeEventListener("resize", updateOverflow);
    }

    return undefined;
  }, [fullText]);

  const handleShowDetails = (event) => {
    event.stopPropagation();
    if (onView) {
      onView(row.data);
    }
  };

  return (
    <div className="flex items-center px-3 py-2">
      <div className="flex items-center min-w-0 gap-2 text-sm text-foreground">
        <span
          ref={textRef}
          className="block min-w-0 flex-1 leading-snug"
          style={collapsedStyle}
        >
          {fullText || "—"}
        </span>
        {canExpand && (
          <button
            type="button"
            onClick={handleShowDetails}
            className="flex-none text-xs font-medium text-primary hover:underline focus:outline-none"
          >
            Show more
          </button>
        )}
      </div>
    </div>
  );
};

const TariffIdCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  const display = row.data?.tariffIdDisplay ?? value;
  const label = display !== undefined && display !== null && display !== "" ? String(display) : "—";
  const formatted = label === "—" ? label : `#${label}`;
  return (
    <div className="flex items-center px-3 py-2">
      <Badge variant="secondary" className="font-mono text-xs">{formatted}</Badge>
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

const CountryCell = ({ row, column, grid, countryMap }) => {
  const value = grid.api.columnField(column, row);
  const iso2 = countryMap?.get(value); // Look up the iso2 code

  return (
    <div className="flex items-center px-3 py-2">
      <div className="flex items-center space-x-2">
        {iso2 ? (
          <img
            src={`https://flagcdn.com/w20/${iso2.toLowerCase()}.png`}
            srcSet={`https://flagcdn.com/w40/${iso2.toLowerCase()}.png 2x`}
            alt={`${value} flag`}
            width="16" // w-4
            height="12" // h-3
            className="rounded-sm object-contain flex-shrink-0"
            onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling.style.display = 'block'; }}
          />
        ) : (
          // Fallback gray dot
          <div className="w-4 h-3 bg-gray-300 dark:bg-gray-700 rounded-sm flex-shrink-0" />
        )}
        <span className="text-sm font-medium">{value || "—"}</span>
      </div>
    </div>
  );
};

const MoneyCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  const n = Number(value);
  const show = Number.isFinite(n) && n !== 0;
  // If column is adValorem, show as percentage
  const isAdValorem = column.id === "adValorem";
  return (
    <div className="flex items-center justify-left px-3 py-2">
      <span className={`font-mono text-sm ${show ? "text-foreground" : "text-muted-foreground"}`}>
        {show
          ? isAdValorem
            ? `${(n * 100).toFixed(2)}%`
            : `$${n.toFixed(2)}`
          : "—"}
      </span>
    </div>
  );
};

const DateCell = ({ row, column, grid }) => {
  const value = grid.api.columnField(column, row);
  let displayDate = "—";
  if (value) {
    try {
      // Assuming value is like "YYYY-MM-DD" from backend LocalDate
      displayDate = new Date(value + 'T00:00:00').toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch (e) {
      console.error("Error formatting date:", value, e);
      displayDate = value; // Fallback to raw value
    }
  }
  return <div className="px-3 py-2 text-sm text-muted-foreground">{displayDate}</div>;
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

const getSortSpecForColumn = (columnId) => {
  switch (columnId) {
    case "tariffid":
    case "adValorem":
    case "specificPerUnit":
      return { kind: "number" };
    default:
      return { kind: "string" };
  }
};

const SortableHeader = ({ column, grid }) => {
  const sortEntry = grid.state.sortModel.useValue().find((c) => c.columnId === column.id);
  const isDescending = sortEntry?.sort?.isDescending ?? false;
  const hasSort = Boolean(sortEntry);

  const handleSort = () => {
    const createSortModel = (overrides = {}) => ({
      columnId: column.id,
      sort: { ...getSortSpecForColumn(column.id), ...overrides },
    });

    if (!hasSort) {
      grid.state.sortModel.set([createSortModel()]);
      return;
    }

    if (!isDescending) {
      grid.state.sortModel.set([createSortModel({ isDescending: true })]);
      return;
    }

    grid.state.sortModel.set([]);
  };

  return (
    <div
      className="flex items-center justify-between px-3 py-3 h-full w-full bg-muted hover:bg-muted/80 cursor-pointer transition-colors border-b border-border font-semibold text-foreground text-sm"
      onClick={handleSort}
    >
      <span>{column.name}</span>
      {hasSort && <div className="ml-2">{!isDescending ? "↑" : "↓"}</div>}
    </div>
  );
};

const StaticHeader = ({ column }) => (
  <div className="flex items-center justify-left px-3 py-3 h-full w-full bg-muted border-b border-border font-semibold text-foreground text-sm">
    <span>{column.name}</span>
  </div>
);

/* ---------------- grid wrapper ---------------- */
//
// Change StaticHeader to SortableHeader to enable sorting
//
function TariffGrid({ userRole, data, onEdit, onDelete, onView, isMobile, countryMap }) {
// Inside the TariffGrid component in Dashboard.jsx

const columns = useMemo(
  () => [
    { id: "tariffid", name: "Tariff ID", width: 120, resizable: true, cellRenderer: TariffIdCell, headerRenderer: StaticHeader },
    { id: "category", name: "Category", width: 180, resizable: true, cellRenderer: CategoryCell, headerRenderer: StaticHeader },
    { id: "descriptionwcountry", name: "Description", width: 400, resizable: true, cellRenderer: (props) => <DescriptionCell {...props} onView={onView} />, headerRenderer: StaticHeader }, // Reduced width slightly
    { id: "partnerCountry", name: "Partner", width: 150, resizable: true, cellRenderer: (props) => <CountryCell {...props} countryMap={countryMap} />, headerRenderer: StaticHeader }, // Shorter name
    { id: "reporterCountry", name: "Reporter", width: 150, resizable: true, cellRenderer: (props) => <CountryCell {...props} countryMap={countryMap} />, headerRenderer: StaticHeader }, // Shorter name
    { id: "adValorem", name: "Ad Valorem", width: 100, resizable: true, cellRenderer: MoneyCell, headerRenderer: StaticHeader }, // Reduced width
    { id: "specificPerUnit", name: "Specific/Unit", width: 110, resizable: true, cellRenderer: MoneyCell, headerRenderer: StaticHeader }, // Reduced width
    { id: "effectivedate", name: "Effective Date", width: 110, resizable: true, cellRenderer: DateCell, headerRenderer: StaticHeader },
    { id: "expirydate", name: "Expiry Date", width: 110, resizable: true, cellRenderer: DateCell, headerRenderer: StaticHeader },
    { id: "datasource", name: "Data Source", width: 150, resizable: true, cellRenderer: TextCell, headerRenderer: StaticHeader },
    { id: "actions", name: "Actions", width: 80, resizable: false, cellRenderer: (p) => <ActionCell {...p} userRole={userRole} onEdit={onEdit} onDelete={onDelete} onView={onView} />, headerRenderer: StaticHeader },
  ],
  [onEdit, onDelete, onView, userRole, countryMap] // Add countryMap dependency
);

  // hook required by the grid library (mounted only when we have data)
  const ds = useClientRowDataSource({ data });

  const baseGridId = useId();

  const grid = Grid.useLyteNyte({
    gridId: `${baseGridId}-${isMobile ? "mobile" : "desktop"}`,
    columns,
    rowDataSource: ds,
    rowHeight: 56,
    headerHeight: 52,
    rowSelection: { mode: "multiple" },
    columnMarkerEnabled: false,
    columnSizeToFit: !isMobile,
    editCellMode: "cell",
    editClickActivator: "double-click",
    columnBase: { editable: false },
  });

  const view = grid.view.useValue();

  return (
    <div className={`border rounded-xl shadow-sm bg-card ${isMobile ? "overflow-x-auto" : "overflow-hidden"}`} style={{ width: "100%", height: "520px" }}>
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
// Replace the existing TariffModal function in Dashboard.jsx with this:
const TariffModal = ({ isOpen, onClose, onSubmit, initialData, isEditing, isLoading, error }) => {
  // --- Define initial state including new fields ---
  const initialFormState = {
    category: "", descriptionwcountry: "", partnerCountry: "", reporterCountry: "",
    adValorem: "", specificPerUnit: "", unitname: "",
    effectivedate: "", expirydate: "", datasource: "" // Added new fields
  };

  const [form, setForm] = useState(initialFormState);
  const [errors, setErrors] = useState({});
  const [countries, setCountries] = useState([]);
  const [loadingCountries, setLoadingCountries] = useState(true);

  // --- Fetch country data ---
  useEffect(() => {
    let isMounted = true; // Flag to prevent state updates on unmounted component
    if (isOpen && countries.length === 0) {
      setLoadingCountries(true);
      fetch('/countries.csv')
        .then(response => {
           if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
           return response.text();
        })
        .then(csvText => {
          Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
              if (!isMounted) return; // Don't update state if component unmounted
              const validCountries = results.data
                .filter(row => row.countryid && row.iso2 && row.name)
                .map(row => ({ iso2: row.iso2.trim(), name: row.name.trim() }))
                .sort((a, b) => a.name.localeCompare(b.name));
              setCountries(validCountries);
              setLoadingCountries(false);
            },
            error: (error) => {
              if (!isMounted) return;
              console.error("Error parsing CSV:", error);
              setCountries([]);
              setLoadingCountries(false);
            }
          });
        })
        .catch(error => {
           if (!isMounted) return;
           console.error("Error fetching countries.csv:", error);
           setCountries([]);
           setLoadingCountries(false);
        });
    }
    // Cleanup function to set the flag when the component unmounts or isOpen changes
    return () => { isMounted = false; };
  }, [isOpen]); // Depend only on isOpen

  // --- Update form state based on initialData ---
  useEffect(() => {
    if (initialData) {
      // Format dates correctly for input type="date" (YYYY-MM-DD)
      // Handles cases where dates might be null or already formatted
      const formattedData = {
        ...initialData,
        effectivedate: initialData.effectivedate ? String(initialData.effectivedate).split('T')[0] : "",
        expirydate: initialData.expirydate ? String(initialData.expirydate).split('T')[0] : "",
        // Ensure other fields are strings or empty strings for controlled inputs
        category: initialData.category || "",
        descriptionwcountry: initialData.descriptionwcountry || "",
        partnerCountry: initialData.partnerCountry || "",
        reporterCountry: initialData.reporterCountry || "",
        adValorem: initialData.adValorem != null ? String(initialData.adValorem) : "",
        specificPerUnit: initialData.specificPerUnit != null ? String(initialData.specificPerUnit) : "",
        unitname: initialData.unitname || "",
        datasource: initialData.datasource || ""
      };
      setForm(formattedData);
    } else {
      setForm(initialFormState); // Reset form for creation
    }
    setErrors({}); // Clear errors when data changes or modal opens/closes
  }, [initialData, isOpen]); // Depend on initialData and isOpen

  // --- Validation ---
  const validateTariffForm = (formData) => {
    const errors = {};
    if (!formData.category || formData.category.trim() === "") errors.category = "Category is required";
    if (!formData.descriptionwcountry || formData.descriptionwcountry.trim() === "") errors.descriptionwcountry = "Description is required";

    // Validate country selections - check if the selected name exists in the fetched list
    if (!formData.partnerCountry || !countries.some(c => c.name === formData.partnerCountry)) {
      errors.partnerCountry = "Partner Country is required and must be selected from the list";
    }
    if (!formData.reporterCountry || !countries.some(c => c.name === formData.reporterCountry)) {
      errors.reporterCountry = "Reporter Country is required and must be selected from the list";
    }

    // Number validations
    const adValoremNum = parseFloat(formData.adValorem);
    if (formData.adValorem && (isNaN(adValoremNum) || adValoremNum < 0)) {
       errors.adValorem = "Ad Valorem must be a valid non-negative number";
    }
    const specificPerUnitNum = parseFloat(formData.specificPerUnit);
     if (formData.specificPerUnit && (isNaN(specificPerUnitNum) || specificPerUnitNum < 0)) {
        errors.specificPerUnit = "Specific per unit must be a valid non-negative number";
     }


    // Optional: Date validation (expiry date must be after effective date if both are set)
    if (formData.effectivedate && formData.expirydate && formData.expirydate < formData.effectivedate) {
      errors.expirydate = "Expiry date cannot be before effective date";
    }
    return errors;
  };

  // --- Handle Submit ---
  const handleSubmit = () => {
    const validationErrors = validateTariffForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});

    // Prepare data for submission: Convert empty dates back to null, numbers to numbers
    const dataToSubmit = {
        ...form,
        adValorem: form.adValorem === "" ? null : parseFloat(form.adValorem),
        specificPerUnit: form.specificPerUnit === "" ? null : parseFloat(form.specificPerUnit),
        effectivedate: form.effectivedate === "" ? null : form.effectivedate,
        expirydate: form.expirydate === "" ? null : form.expirydate,
        // datasource can remain as is (empty string or value)
    };

    onSubmit(dataToSubmit);
  };

  // Check if form has changes compared to initial data (for disabling update button)
  const hasChanges = useMemo(() => {
      if (!isEditing || !initialData) return true; // Always enable for create mode

       // Format initial dates for comparison
       const initialFormatted = {
           ...initialData,
           effectivedate: initialData.effectivedate ? String(initialData.effectivedate).split('T')[0] : "",
           expirydate: initialData.expirydate ? String(initialData.expirydate).split('T')[0] : "",
           adValorem: initialData.adValorem != null ? String(initialData.adValorem) : "",
           specificPerUnit: initialData.specificPerUnit != null ? String(initialData.specificPerUnit) : "",
       };

      // Compare relevant fields, ensure types match (mostly strings due to form state)
      for (const key in initialFormState) {
          if (String(form[key] ?? "") !== String(initialFormatted[key] ?? "")) {
               // console.log(`Difference found in key: ${key}, Form: "${form[key]}", Initial: "${initialFormatted[key]}"`);
              return true;
          }
      }
      return false; // No changes detected
  }, [form, initialData, isEditing, initialFormState]);


  const categories = ["COMPOSITE", "SPECIFIC_PER_UNIT", "AD_VALOREM"];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">{isEditing ? "Edit Tariff Entry" : "Create New Tariff Entry"}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 py-6 max-h-[70vh] overflow-y-auto pr-3"> {/* Added scroll */}
          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category <span className="text-red-500">*</span></Label>
            <Select value={form.category || ""} onValueChange={(value) => setForm((f) => ({ ...f, category: value }))}>
              <SelectTrigger id="category" className={cn(errors.category ? "border-red-500" : "")}>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>{categories.map((cat) => <SelectItem key={cat} value={cat}>{cat.replace(/_/g, " ")}</SelectItem>)}</SelectContent>
            </Select>
            {errors.category && <p className="text-sm text-red-500">{errors.category}</p>}
          </div>

          {/* Unit Name */}
          <div className="space-y-2">
            <Label htmlFor="unitname">Unit Name</Label>
            <Input id="unitname" value={form.unitname || ""} onChange={(e) => setForm((f) => ({ ...f, unitname: e.target.value }))} placeholder="e.g., kg, liter, piece" />
             {/* No error display needed unless you add validation */}
          </div>


          {/* Description - Spanning full width */}
          <div className="md:col-span-2 space-y-2">
            <Label htmlFor="descriptionwcountry">Description <span className="text-red-500">*</span></Label>
            <Input id="descriptionwcountry" value={form.descriptionwcountry || ""} onChange={(e) => setForm((f) => ({ ...f, descriptionwcountry: e.target.value }))} className={cn(errors.descriptionwcountry ? "border-red-500" : "")} placeholder="e.g., Industrial Machinery" />
            {errors.descriptionwcountry && <p className="text-sm text-red-500">{errors.descriptionwcountry}</p>}
          </div>

          {/* Partner Country */}
          <CountrySelector
            id="partnerCountry"
            label="Partner Country"
            value={form.partnerCountry || ""}
            onChange={(countryName) => setForm((f) => ({ ...f, partnerCountry: countryName }))}
            countries={countries}
            error={errors.partnerCountry}
            placeholder={loadingCountries ? "Loading..." : "Select partner country"}
            required={true}
            disabled={loadingCountries}
          />

          {/* Reporter Country */}
          <CountrySelector
            id="reporterCountry"
            label="Reporter Country"
            value={form.reporterCountry || ""}
            onChange={(countryName) => setForm((f) => ({ ...f, reporterCountry: countryName }))}
            countries={countries}
            error={errors.reporterCountry}
            placeholder={loadingCountries ? "Loading..." : "Select reporter country"}
            required={true}
            disabled={loadingCountries}
          />

          {/* Ad Valorem Rate */}
          <div className="space-y-2">
             <Label htmlFor="adValorem">Ad Valorem Rate (Decimal)</Label>
             <Input id="adValorem" type="number" step="0.0001" min="0" value={form.adValorem || ""} onChange={(e) => setForm((f) => ({ ...f, adValorem: e.target.value }))} className={cn(errors.adValorem ? "border-red-500" : "")} placeholder="e.g., 0.055 for 5.5%" />
             {errors.adValorem && <p className="text-sm text-red-500">{errors.adValorem}</p>}
           </div>


           {/* Specific per Unit */}
           <div className="space-y-2">
             <Label htmlFor="specificPerUnit">Specific per Unit ($)</Label>
             <Input id="specificPerUnit" type="number" step="0.01" min="0" value={form.specificPerUnit || ""} onChange={(e) => setForm((f) => ({ ...f, specificPerUnit: e.target.value }))} className={cn(errors.specificPerUnit ? "border-red-500" : "")} placeholder="e.g., 12.50" />
             {errors.specificPerUnit && <p className="text-sm text-red-500">{errors.specificPerUnit}</p>}
           </div>

          <div className="space-y-2">
            <Label htmlFor="effectivedate">Effective Date</Label>
            <Input id="effectivedate" type="date" value={form.effectivedate || ""} onChange={(e) => setForm((f) => ({ ...f, effectivedate: e.target.value }))} className={cn(errors.effectivedate ? "border-red-500" : "")}/>
            {errors.effectivedate && <p className="text-sm text-red-500">{errors.effectivedate}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="expirydate">Expiry Date</Label>
            <Input id="expirydate" type="date" value={form.expirydate || ""} onChange={(e) => setForm((f) => ({ ...f, expirydate: e.target.value }))} className={cn(errors.expirydate ? "border-red-500" : "")}/>
            {errors.expirydate && <p className="text-sm text-red-500">{errors.expirydate}</p>}
          </div>

          <div className="md:col-span-2 space-y-2"> {/* Span across both columns */}
            <Label htmlFor="datasource">Data Source</Label>
            <Input id="datasource" value={form.datasource || ""} onChange={(e) => setForm((f) => ({ ...f, datasource: e.target.value }))} placeholder="e.g., Government Gazette, WTO Schedule" />
             {/* No error display needed unless you add validation */}
          </div>

          {/* Mandatory Fields Note */}
          <div className="md:col-span-2 text-sm text-muted-foreground mt-2">
            <span className="text-red-500 mr-1">*</span>
            <span>Starred fields are mandatory</span>
         </div>
        </div>

        {error && <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-md mb-4"><p className="text-sm text-red-600 dark:text-red-400">{error}</p></div>}

        <DialogFooter className="flex gap-3 pt-4 border-t"> {/* Added padding top and border */}
          <Button variant="outline" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading || (isEditing && !hasChanges)}>
            {isLoading ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />{isEditing ? "Updating..." : "Creating..."}</>) : (<><Check className="mr-2 h-4 w-4" />{isEditing ? "Update" : "Create"}</>)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Replace the existing ViewDetailsModal function in Dashboard.jsx with this:
const ViewDetailsModal = ({ isOpen, onClose, data }) => {
  const navigate = useNavigate();

  // Helper function to format date string (YYYY-MM-DD) nicely
  const formatDateForView = (dateString) => {
    if (!dateString) return "—"; // Handle null or empty string
    try {
      // Add time part to ensure correct date parsing across timezones
      const date = new Date(dateString + 'T00:00:00');
      // Check if the date is valid after parsing
      if (isNaN(date.getTime())) {
          return dateString; // Return original string if invalid
      }
      return date.toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric'
      });
    } catch (e) {
      console.error("Error formatting date:", dateString, e);
      return dateString; // Fallback to raw value on error
    }
  };


  const getValidTariffId = () => {
    if (!data) return null;
    const numericId = Number(data.tariffid);
    if (Number.isFinite(numericId) && numericId > 0) return numericId;
    const id = data.tariffIdDisplay ?? data.id;
    if (id === undefined || id === null || String(id).trim() === "") return null;
    return id;
  };

  const viewInCalculator = () => {
    const tariffId = getValidTariffId();
    if (!tariffId) return;
    // Use state for prefill instead of query params if possible, depends on Calculator logic
    // For simplicity, sticking to query param as in original code
     navigate(`/calculator`, { state: { prefill: { tariffId: String(tariffId) } } });
     onClose(); // Close modal after navigating
  };

  const viewInHistorical = () => {
    if (!data) return;
    // Prefer the display ID for consistency if available
    const tariffId = data.tariffIdDisplay ?? data.tariffid;
     if (!tariffId) return; // Don't navigate if no ID
    navigate(`/historical?tariffId=${encodeURIComponent(tariffId)}`);
     onClose(); // Close modal after navigating
  };

  if (!data) return null; // Render nothing if no data

  // Determine the badge label safely
  const detailBadgeLabel = (() => {
    const idValue = data.tariffIdDisplay ?? data.tariffid;
    return idValue != null && String(idValue).trim() !== "" ? `#${idValue}` : "—";
  })();

  // Format AdValorem as percentage
   const formatAdValorem = (value) => {
       const num = parseFloat(value);
       if (isNaN(num)) return "—";
       // Assuming backend sends 0.05 for 5%
       return `${(num * 100).toFixed(2).replace(/\.00$/, '')}%`;
   };

   // Format SpecificPerUnit as currency
   const formatSpecific = (value) => {
       const num = parseFloat(value);
       if (isNaN(num)) return "—";
       return `$${num.toFixed(2)}`;
   };


  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Badge variant="secondary" className="font-mono">{detailBadgeLabel}</Badge>
            <span>Tariff Details</span>
          </DialogTitle>
        </DialogHeader>
        {/* Added scroll container */}
        <div className="space-y-6 py-6 max-h-[70vh] overflow-y-auto pr-3">
          {/* Category & Unit */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Category</Label>
              <div className="mt-1">
                <Badge variant="outline">{data.category?.replace(/_/g, " ") || "—"}</Badge>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Unit Name</Label>
              <p className="mt-1 text-sm">{data.unitname || "—"}</p>
            </div>
          </div>

          {/* Description */}
          <div>
            <Label className="text-sm font-medium text-muted-foreground">Description</Label>
            <div
              className="mt-1 text-sm bg-muted/30 p-3 rounded-md border max-h-40 overflow-y-auto whitespace-pre-wrap leading-relaxed"
              style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
            >
              {data.descriptionwcountry || "—"}
            </div>
          </div>

          {/* Countries */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Partner Country</Label>
              {/* Note: Flag display might require fetching countryMap here too, simplified for now */}
              <div className="mt-1 flex items-center space-x-2">
                <div className="w-4 h-3 bg-muted rounded-sm" />
                <span className="text-sm">{data.partnerCountry || "—"}</span>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-muted-foreground">Reporter Country</Label>
              <div className="mt-1 flex items-center space-x-2">
                 <div className="w-4 h-3 bg-muted rounded-sm" />
                <span className="text-sm">{data.reporterCountry || "—"}</span>
              </div>
            </div>
          </div>

          {/* Rates */}
          <div className="grid grid-cols-2 gap-6">
            <div>
               <Label className="text-sm font-medium text-muted-foreground">Ad Valorem Rate</Label>
               <p className="mt-1 text-lg font-mono text-foreground">{formatAdValorem(data.adValorem)}</p>
             </div>
             <div>
               <Label className="text-sm font-medium text-muted-foreground">Specific per Unit</Label>
               <p className="mt-1 text-lg font-mono text-foreground">{formatSpecific(data.specificPerUnit)}</p>
             </div>
          </div>

           {/* --- NEW DETAILS SECTIONS --- */}
            <div className="grid grid-cols-2 gap-6 border-t pt-4">
               <div>
                  <Label className="text-sm font-medium text-muted-foreground">Effective Date</Label>
                  <p className="mt-1 text-sm">{formatDateForView(data.effectivedate)}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Expiry Date</Label>
                  <p className="mt-1 text-sm">{formatDateForView(data.expirydate)}</p>
                </div>
            </div>
            <div className="border-t pt-4">
               <Label className="text-sm font-medium text-muted-foreground">Data Source</Label>
               <p className="mt-1 text-sm">{data.datasource || "—"}</p>
            </div>

        </div> {/* End scroll container */}

        <DialogFooter className="pt-4 border-t"> {/* Add border */}
          <Button onClick={viewInCalculator} variant="outline" size="sm" disabled={!getValidTariffId()}>View in Calculator</Button>
          <Button onClick={viewInHistorical} variant="outline" size="sm" disabled={!getValidTariffId()}>View Historical</Button>
          <Button onClick={onClose} size="sm">Close</Button> {/* Changed variant */}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/* ---------------- main ---------------- */
export default function Dashboard() {
  const [mode, setMode] = useState("desc");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize] = useState(50);
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
  const [countries, setCountries] = useState([]);
  const [loadingCountries, setLoadingCountries] = useState(true);

  const isMobile = useMediaQuery("(max-width: 768px)");

const debouncedQuery = useDebounce(query);

  // Create a lookup map for country names to iso2 codes
  const countryMap = useMemo(() => {
    if (loadingCountries || countries.length === 0) return new Map();
    return new Map(countries.map(c => [c.name, c.iso2]));
  }, [countries, loadingCountries]);

  const userRole = JSON.parse(localStorage.getItem("user")).role;

  // Reset page when filters change
  // Fetch countries for the grid flags
  useEffect(() => {
    setLoadingCountries(true);
    fetch('/countries.csv')
      .then(response => {
         if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
         return response.text();
      })
      .then(csvText => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            const validCountries = results.data
              .filter(row => row.countryid && row.iso2 && row.name)
              .map(row => ({
                iso2: row.iso2.trim(),
                name: row.name.trim()
              }));
            setCountries(validCountries);
            setLoadingCountries(false);
          },
          error: (error) => {
            console.error("Error parsing CSV:", error);
            setCountries([]);
            setLoadingCountries(false);
          }
        });
      })
      .catch(error => {
         console.error("Error fetching countries.csv:", error);
         setCountries([]);
         setLoadingCountries(false);
      });
  }, []); // Runs once on mount

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
      const { data } = await getDashboardData(params);

      // Normalize fields so they always match our column IDs
      const mappedContent = (Array.isArray(data.content) ? data.content : []).map((row) => {
        const rawTariffId = row.tariffid ?? row.tariffId ?? row.id ?? "";
        const tariffIdString = rawTariffId != null ? String(rawTariffId) : "";
        const tariffIdNumber = Number(tariffIdString);
        const normalizedTariffId = Number.isFinite(tariffIdNumber) ? tariffIdNumber : tariffIdString;
        return {
          id: tariffIdString, // Use the string ID for consistency in the grid row key
          tariffid: normalizedTariffId, // Keep numeric if possible for potential sorting
          tariffIdDisplay: tariffIdString, // Always show the original string ID
          category: row.category ?? "",
          descriptionwcountry: row.descriptionwcountry ?? row.descriptionWCountry ?? row.description ?? "",
          partnerCountry: row.partnerCountry ?? "", // Ensure name is used
          reporterCountry: row.reporterCountry ?? "", // Ensure name is used
          adValorem: row.adValorem ?? row.adValorem ?? "",
          specificPerUnit: row.specificPerUnit ?? row.specificPerUnit ?? "",
          unitname: row.unitname ?? row.unitName ?? "",
          effectivedate: row.effectivedate ?? null, // Expecting YYYY-MM-DD string or null
          expirydate: row.expirydate ?? null,     // Expecting YYYY-MM-DD string or null
          datasource: row.datasource ?? ""
        };
      }).sort((a, b) => {
        const aId = typeof a.tariffid === "number" ? a.tariffid : Number(a.tariffid);
        const bId = typeof b.tariffid === "number" ? b.tariffid : Number(b.tariffid);
        const aIsNumber = Number.isFinite(aId);
        const bIsNumber = Number.isFinite(bId);
        if (aIsNumber && bIsNumber) return aId - bId;
        if (aIsNumber) return -1;
        if (bIsNumber) return 1;
        return String(a.tariffid).localeCompare(String(b.tariffid));
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
      // Helper to format date strings (YYYY-MM-DD) for CSV
      const formatDateForCSV = (dateString) => {
        if (!dateString) return ""; // Return empty string for null/undefined dates
        try {
          // Add time part to prevent timezone issues during parsing
          const date = new Date(dateString + 'T00:00:00');
          // Check if the date is valid
          if (isNaN(date.getTime())) {
              return dateString; // Return original string if invalid
          }
          // Format as locale date string (e.g., MM/DD/YYYY or DD/MM/YYYY based on locale)
          return date.toLocaleDateString();
        } catch (e) {
          console.error("Error formatting date for CSV:", dateString, e);
          return dateString; // Fallback to raw value on error
        }
      };

      try {
        setIsDownloading(true); // Assuming you have this state setter
        // --- Fetch ALL tariff data ONCE ---
        // Backend should return { tariffs: [...] } when size=-1
        const { data } = await getDashboardData(new URLSearchParams("size=-1"));

        // --- Use the data from the single API call ---
        const allTariffsData = Array.isArray(data?.tariffs) ? data.tariffs : [];

        if (allTariffsData.length === 0) {
          toast.info("No tariff data available to export.");
          setIsDownloading(false); // Reset loading state
          return; // Exit if no data
        }

        // Define the fields you want to export and their CSV header labels
        const fields = [
          // --- Use 'tariffId' as the key from TariffPatchDTO ---
          { key: 'tariffId', label: 'Tariff ID' },
          { key: 'descriptionwcountry', label: 'Description' },
          { key: 'partnerCountry', label: 'Partner Country' },
          { key: 'reporterCountry', label: 'Reporter Country' },
          { key: 'unitname', label: 'Unit Name' },
          { key: 'category', label: 'Category' },
          { key: 'adValorem', label: 'Ad Valorem Rate' }, // Changed label slightly
          { key: 'specificPerUnit', label: 'Specific Per Unit Rate' }, // Changed label slightly
          { key: 'effectivedate', label: 'Effective Date' },
          { key: 'expirydate', label: 'Expiry Date' },
          { key: 'datasource', label: 'Data Source' }
        ];

        // Transform data for CSV, applying formatting
        const transformedData = allTariffsData.map(item => {
          const transformed = {};
          fields.forEach(field => {
            let value = item[field.key]; // Directly use the key defined in fields

            // Format dates
            if ((field.key === 'effectivedate' || field.key === 'expirydate') && value) {
              transformed[field.label] = formatDateForCSV(value);
            }
            // Format Ad Valorem as percentage string if it exists
            else if (field.key === 'adValorem' && value != null) {
                const num = parseFloat(value);
                // Display as percentage
                transformed[field.label] = !isNaN(num) ? `${(num * 100).toFixed(2)}%` : '';
            }
            // Keep Specific Per Unit as number string (formatted to 2 decimals)
            else if (field.key === 'specificPerUnit' && value != null) {
                const num = parseFloat(value);
                // Format as number string
                transformed[field.label] = !isNaN(num) ? num.toFixed(2) : '';
            }
            // Handle other fields (null/undefined become empty string)
            else {
              transformed[field.label] = value ?? '';
            }
          });
          return transformed;
        });

        // Convert to CSV using Papaparse
        const csv = Papa.unparse(transformedData, {
          header: true, // Use field.label as headers
          skipEmptyLines: true
        });

        // Create Blob and trigger download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Use date-fns or similar for more robust date formatting if needed
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        a.download = `tariffs_${timestamp}.csv`;
        document.body.appendChild(a); // Append to body for Firefox compatibility
        a.click();
        document.body.removeChild(a); // Clean up
        window.URL.revokeObjectURL(url);

        // --- Use the length of the actual exported data array ---
        toast.success(`Exported ${allTariffsData.length} tariff records`);

      } catch (err) {
        if (err.response?.status === 401) {
          setShowRelogin(true); // Assuming you have this state setter
          return;
        }
        console.error('Download failed:', err);
        toast.error('Failed to export data. See console for details.');
      } finally {
        setIsDownloading(false); // Assuming you have this state setter
      }
  };

  const closeDialogs = () => {
    setShowCreate(false); setShowEdit(false); setShowDelete(false); setShowView(false);
    setSelectedRow(null); setActionError("");
  };

  const onSaveChanges = async (formData) => {
    setActionLoading(true); setActionError("");
    console.log("Form data to submit:", formData);
    delete formData.tariffid;
    delete formData.tariffIdDisplay;
    try {
      if (showEdit) {
        console.log("Updating tariff with ID:", selectedRow.id, "and data:", formData);
        await updateTariff(selectedRow.id, formData);
        toast.success("Tariff updated successfully");
      } else {
        console.log("Creating tariff with data:", formData);
        await createTariff(formData);
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
      await deleteTariff(selectedRow.id);
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

        <CardContent className="px-0 pt-4 md:pt-6 pb-6 md:pb-8">
          <div className="px-4 md:px-6">
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
              <TariffGrid 
              userRole={userRole} 
              data={results.content} 
              onEdit={handleEdit} 
              onDelete={handleDelete} 
              onView={handleView} 
              isMobile={isMobile}
              countryMap={countryMap}
            />
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
            <div className="flex flex-col gap-4 pt-6 border-t px-4 md:px-6 md:flex-row md:items-center md:justify-between">
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                <span>Showing page {page + 1} of {results.totalPages}</span>
                <Badge variant="outline" className="text-xs">{results.content.length} records</Badge>
              </div>

              <div className="overflow-x-auto">
                <div className="flex items-center gap-2 min-w-max">
                  <Button variant="outline" size="sm" disabled={page <= 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
                  <div className="flex items-center gap-1">
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
                  {(() => {
                    const idValue = selectedRow.tariffIdDisplay ?? selectedRow.tariffid;
                    const badgeLabel = idValue ? `#${idValue}` : "—";
                    return <Badge variant="secondary" className="font-mono">{badgeLabel}</Badge>;
                  })()}
                  <div
                    className="text-sm text-muted-foreground block min-w-0 flex-1 leading-snug"
                    style={{
                      maxWidth: "600px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      whiteSpace: "normal",
                      wordBreak: "break-word",
                      WebkitMaskImage: "linear-gradient(90deg, #000 85%, rgba(0,0,0,0))",
                      maskImage: "linear-gradient(90deg, #000 85%, rgba(0,0,0,0))",
                    }}
                  >
                    {selectedRow.descriptionwcountry || "—"}
                  </div>
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
