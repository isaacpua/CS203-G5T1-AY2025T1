import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "../components/ui/select";
import { getTariffHistory, getTariffRecommendations } from "../api/axiosClient";
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { Relogin } from "@/components/Relogin";



function Field({ id, label, children }) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}

export default function HistoricalTariffExplorer() {
  const [form, setForm] = useState({
    reporter: "",
    partner: "",
    itemCode: "",
    start: "",
    end: "",
    unit: "percent",
  });

  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [series, setSeries] = useState(null);
  const [error, setError] = useState("");

  const [showRelogin, setShowRelogin] = useState(false);



// this part is to bullshit the recommended suggestions, we should add more to make it more full and make it more legit 
  useEffect(() => {
    (async () => {
      try {
        const { data } = await getTariffRecommendations();
        setSuggestions(data || []);
      } catch (e) {
        if (e.response?.status === 401) {
          console.log("found 401 error wow")
          setShowRelogin(true);
          return;
        }
        console.error(e);
      }
    })();
  }, []);

  async function fetchHistory(params) {
    try {
      setLoading(true);
      setError("");
      const { data } = await getTariffHistory(params);
      setSeries(data);
    } catch (e) {
      if (e.response?.status === 401) {
        console.log("found 401 error wow")
        setShowRelogin(true);
        return;
      }
      setError("No historical data found.");
      setSeries(null);
    } finally {
      setLoading(false);
    }
  }

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    fetchHistory(form);
  }

  if (series) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Tariff History</CardTitle>
          <CardDescription>{form.reporter} → {form.partner} ({form.itemCode})</CardDescription>
          <Button variant="outline" onClick={() => setSeries(null)}>Back</Button>
        </CardHeader>
        <CardContent className="h-[360px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={series.points || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
    {showRelogin && <Relogin />}
    <Card>
      <CardHeader>
        <CardTitle>Enter Data</CardTitle>
        <CardDescription>Select parameters to fetch historical tariffs</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
          <Field id="reporter" label="Reporter">
            <Input id="reporter" name="reporter" value={form.reporter} onChange={handleChange} />
          </Field>
          <Field id="partner" label="Partner">
            <Input id="partner" name="partner" value={form.partner} onChange={handleChange} />
          </Field>
          <Field id="itemCode" label="Item Code">
            <Input id="itemCode" name="itemCode" value={form.itemCode} onChange={handleChange} />
          </Field>
          <Field id="start" label="Start Date">
            <Input id="start" type="date" name="start" value={form.start} onChange={handleChange} />
          </Field>
          <Field id="end" label="End Date">
            <Input id="end" type="date" name="end" value={form.end} onChange={handleChange} />
          </Field>
          <Field id="unit" label="Unit">
            <Select value={form.unit} onValueChange={(v) => setForm((f) => ({ ...f, unit: v }))}>
              <SelectTrigger><SelectValue placeholder="Select unit" /></SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Unit</SelectLabel>
                  <SelectItem value="percent">Percent</SelectItem>
                  <SelectItem value="value">Value</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
          <Button type="submit" disabled={loading}>
            {loading ? "Loading..." : "Get History"}
          </Button>
        </form>

        {error && <div className="text-red-500 mt-2">{error}</div>}

        <div className="mt-6">
          <div className="text-sm mb-2 text-muted-foreground">Recommended</div>
          <div className="grid gap-3 md:grid-cols-2">
            {suggestions.map((s, i) => (
              <Card key={i} onClick={() => fetchHistory(s)} className="p-3 cursor-pointer hover:ring-1 hover:ring-primary">
                <CardTitle className="text-sm">{s.title || s.itemCode}</CardTitle>
                <CardDescription className="text-xs">{s.reporter} → {s.partner}</CardDescription>
              </Card>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
    </>
  );
}
