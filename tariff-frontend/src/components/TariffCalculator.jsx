import { useState } from 'react';
import axiosClient from '../api/axiosClient';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Terminal } from "lucide-react";

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

    const requestData = {
      productCategory: productCategory,
      value: value,
      fromCountry: "USA",
      toCountry: "Canada"
    };

    try {
      const response = await axiosClient.post('/tariffs/calculate', requestData);
      setResult(response.data);
    } catch (err) {
      setError('Failed to calculate tariff. Please ensure the backend is running and reachable.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full md:w-[450px]">
      <CardHeader>
        <CardTitle>TARIFF Calculator</CardTitle>
        <CardDescription>Calculate import tariffs for your products.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="category">Product Category</Label>
              <Select onValueChange={setProductCategory} defaultValue={productCategory}>
                <SelectTrigger id="category">
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent position="popper">
                  <SelectItem value="electronics">Electronics</SelectItem>
                  <SelectItem value="automotive">Automotive</SelectItem>
                  <SelectItem value="apparel">Apparel</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
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
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Please wait
                </>
              ) : (
                'Calculate Tariff'
              )}
            </Button>
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex flex-col items-start pt-6">
        {result && (
          <Alert variant="default" className="w-full">
            <Terminal className="h-4 w-4" />
            <AlertTitle>Calculation Successful!</AlertTitle>
            <AlertDescription className="font-mono">
              <div>Calculated Tariff: ${result.calculatedTariff.toFixed(2)}</div>
              <div>Total Value: ${result.totalValue.toFixed(2)}</div>
            </AlertDescription>
          </Alert>
        )}
        {error && (
          <Alert variant="destructive" className="w-full">
            <Terminal className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
        )}
      </CardFooter>
    </Card>
  );
}

export default TariffCalculator;
