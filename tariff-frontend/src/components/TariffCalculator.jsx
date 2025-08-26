import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function TariffCalculator() {
  const [productCategory, setProductCategory] = useState('electronics');
  const [value, setValue] = useState(1000);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    // We will add the API call logic here in the next step
    console.log("Submitting:", { productCategory, value });
  };

  return (
    <Card className="w-[450px] mx-auto my-12">
      <CardHeader>
        <CardTitle>TARIFF Calculator</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="category">Product Category</Label>
              <Input 
                id="category" 
                placeholder="e.g., electronics"
                value={productCategory}
                onChange={(e) => setProductCategory(e.target.value)} 
              />
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="value">Product Value ($)</Label>
              <Input 
                id="value" 
                type="number"
                placeholder="e.g., 1000" 
                value={value}
                onChange={(e) => setValue(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full">Calculate Tariff</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export default TariffCalculator;