import React, { useState, useMemo } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// CountryList Component
function CountryList({ countries, loadingCountries }) {
  const [searchTerm, setSearchTerm] = useState('');
  const lowerSearchTerm = searchTerm.toLowerCase();

  // We need to check if any matches exist for the "No countries found" message
  const matchesFound = useMemo(() => {
    if (loadingCountries || countries.length === 0) return false;
    if (searchTerm === '') return true; // All countries are shown
    // Check if at least one country matches
    return countries.some(c => c.name.toLowerCase().includes(lowerSearchTerm));
  }, [countries, loadingCountries, searchTerm, lowerSearchTerm]);

  const handleSearchInputChange = (e) => {
    setSearchTerm(e.target.value);
  };

  return (
    <>
      <div className="p-2 sticky top-0 bg-popover z-10">
        <Input
          type="search"
          placeholder="Search countries..."
          value={searchTerm}
          onChange={handleSearchInputChange}
          // We still need these to prevent the dropdown from
          // closing when we click/interact with the input.
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
          // The key captures are also good to keep to prevent
          // the Select's built-in type-ahead.
          onKeyDownCapture={(e) => e.stopPropagation()}
          onKeyUpCapture={(e) => e.stopPropagation()}
          className="h-8 text-sm w-full"
          aria-label="Search countries"
        />
      </div>

      {loadingCountries ? (
          <div className="p-2 text-sm text-muted-foreground text-center">Loading countries...</div>
      ) : !matchesFound ? ( // Use our memoized boolean
          <div className="p-2 text-sm text-muted-foreground text-center">No countries found.</div>
      ) : (
          <div className="max-h-[200px] overflow-y-auto">
              {/* // Map over ALL countries, not the filtered list. This keeps the child array stable for the Select component. */}
            {countries.map((country) => {
              // Check if this country should be visible
              const isMatch = searchTerm === '' || country.name.toLowerCase().includes(lowerSearchTerm);
              
              return (
                <SelectItem
                  key={country.iso2}
                  value={country.name}
                  // Conditionally hide the item using the 'hidden' attribute.
                  // This keeps it in the DOM but invisible, solving the focus issue.
                  hidden={!isMatch}
                  // We must also manually set display, as 'hidden'
                  // adds 'display: none' which can be hard to override.
                  style={{ display: isMatch ? 'flex' : 'none' }}
                >
                  <div className="flex items-center gap-2">
                    <img
                      src={`https://flagcdn.com/w20/${country.iso2.toLowerCase()}.png`}
                      srcSet={`https://flagcdn.com/w40/${country.iso2.toLowerCase()}.png 2x`}
                      alt={`${country.name} flag`}
                      width="20"
                      className="rounded-sm object-contain flex-shrink-0"
                      loading="lazy"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                    <span>{country.name}</span>
                  </div>
                </SelectItem>
              );
            })}
          </div>
      )}
    </>
  );
}

// --- CountrySelector Component  ---
function CountrySelector({
  id,
  label,
  value,
  onChange,
  placeholder = "Select country",
  countries = [],
  error,
  required = false,
  className,
  disabled = false,
  loadingCountries = false,
}) {
  const selectedCountry = useMemo(() => countries.find(c => c.name === value), [countries, value]);

  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>
        {label} {required && <span className="text-red-500">*</span>}
      </Label>
      <Select
        value={value}
        onValueChange={onChange}
        disabled={disabled || loadingCountries || countries.length === 0}
      >
        <SelectTrigger id={id} className={cn(error ? "border-red-500" : "")}>
          <SelectValue placeholder={placeholder}>
            {selectedCountry ? (
              <div className="flex items-center gap-2 text-sm">
                <img
                  src={`https://flagcdn.com/w20/${selectedCountry.iso2.toLowerCase()}.png`}
                  srcSet={`https://flagcdn.com/w40/${selectedCountry.iso2.toLowerCase()}.png 2x`}
                  alt={`${selectedCountry.name} flag`}
                  width="20"
                  className="rounded-sm object-contain flex-shrink-0"
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
                <span className="truncate">{selectedCountry.name}</span>
              </div>
            ) : (
              <span className="text-muted-foreground text-sm">{placeholder}</span>
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <CountryList
            countries={countries}
            loadingCountries={loadingCountries}
          />
        </SelectContent>
      </Select>
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
}

export default CountrySelector;