import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select.jsx"; // This path is correct relative to src/components/

export default function CountrySelector({ countries, value, onChange, placeholder = "Select a country..." }) {
  
  // The 'value' prop for <Select> must be a string.
  // We'll use the country's `value` (which is the ID) as the string value.
  const stringValue = value ? String(value.value) : undefined;

  const handleValueChange = (val) => {
    // Find the full country object that matches the selected string value
    const selectedCountry = countries.find(c => String(c.value) === val);
    if (selectedCountry) {
      onChange(selectedCountry);
    }
  };

  return (
    <Select value={stringValue} onValueChange={handleValueChange}>
      <SelectTrigger className="w-full justify-between font-normal">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent className="max-h-60">
        {countries.length > 0 ? (
          countries.map((country) => (
            <SelectItem 
              key={country.value} 
              value={String(country.value)} // Value must be a string
            >
              {country.label}
            </SelectItem>
          ))
        ) : (
          // Show a message if the list is empty
          <div className="p-4 text-sm text-muted-foreground text-center">
            No countries found.
          </div>
        )}
      </SelectContent>
    </Select>
  )
}