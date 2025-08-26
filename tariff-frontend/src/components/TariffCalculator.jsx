import { useState } from 'react';
import axiosClient from '../api/axiosClient'; // Import our new Axios client
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function TariffCalculator() {
  const [productCategory, setProductCategory] = useState('electronics');
  const [value, setValue] = useState(1000);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setResult(null);
    setError('');

    // This object structure must match your `TariffRequest.java` model
    const requestData = {
      productCategory: productCategory,
      value: value,
      fromCountry: "USA", // Mock data as per our simplified logic
      toCountry: "Canada"   // Mock data as per our simplified logic
    };

    try {
      // Make the POST request to the /tariffs/calculate endpoint
      const response = await axiosClient.post('/tariffs/calculate', requestData);
      setResult(response.data); // Save the successful response data
    } catch (err) {
      setError('Failed to calculate tariff. Please check the console and make sure the backend is running.');
      console.error(err);
    } finally {
      setIsLoading(false); // Stop the loading indicator
    }
  };

  return (
    <Card className="w-[450px] mx-auto my-12">
      <CardHeader>
        <CardTitle>TARIFF Calculator</CardTitle>
        <CardDescription>Calculate import tariffs for your products.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="category">Product Category</Label>
              <Input
                id="category"
                placeholder="e.g., electronics, automotive"
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
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Calculating...' : 'Calculate Tariff'}
            </Button>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex flex-col items-start">
        {/* Display the result if it exists */}
        {result && (
          <div className="mt-4 p-4 bg-green-100 rounded-md w-full">
            <h3 className="font-bold text-green-800">Calculation Result:</h3>
            <p>Calculated Tariff: ${result.calculatedTariff.toFixed(2)}</p>
            <p>Total Value: ${result.totalValue.toFixed(2)}</p>
          </div>
        )}
        {/* Display an error message if it exists */}
        {error && <p className="mt-4 text-red-500">{error}</p>}
      </CardFooter>
    </Card>
  );
}

export default TariffCalculator;