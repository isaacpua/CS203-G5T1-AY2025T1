import React, { useState } from "react";
import { postAnalyzable } from "@/api/axiosClient";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTheme } from "@/components/theme-provider";
import { Spinner } from "@/components/ui/shadcn-io/spinner";

export default function Analyzer() {

  const tester = "**Summary Overview**  \nThe article discusses China's decision to suspend certain retaliatory tariffs on U.S. agricultural imports following a meeting between U.S. President Donald Trump and Chinese President Xi Jinping. However, tariffs on U.S. soybeans remain in place, affecting trade dynamics.\n\n**Tariff Changes Detected**  \n- **Product or Sector**: Certain U.S. agricultural goods  \n  - **Change Type**: Removal  \n  - **New Rate or Change Description**: Removal of duties up to 15%  \n  - **Country or Region Involved**: China, United States\n\n- **Product or Sector**: U.S. soybeans  \n  - **Change Type**: No change (remains)  \n  - **New Rate or Change Description**: 13% tariff remains  \n  - **Country or Region Involved**: China, United States\n\n- **Product or Sector**: U.S. goods (general)  \n  - **Change Type**: Suspension  \n  - **New Rate or Change Description**: Suspension of 24% additional tariffs for one year  \n  - **Country or Region Involved**: China, United States\n\n**Effective Dates or Timelines**  \n- Removal of duties on certain agricultural goods effective from November 10, 2025.  \n- Suspension of 24% additional tariffs for one year (starting unspecified).\n\n**Sources or References**  \n- State Council's tariff commission (China)  \n- White House (United States)  \n- Reuters article by Joe Cash, Ella Cao, and Ethan Wang\n\n**Confidence Notes**  \n- The specific agricultural goods affected by the removal of duties up to 15% are not detailed in the article."
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const { theme } = useTheme();
  const prefersDark =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = theme === "dark" || (theme === "system" && prefersDark);

  const canAnalyze = url.trim() !== "" || text.trim() !== "";

  async function handleAnalyze() {
    if (!canAnalyze) {
      setError("Please provide a URL or text to analyze.");
      return;
    }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const payload = { url: url || null, text: text || null };
      const res = await postAnalyzable(payload);
      setResult(res.data.markdown);
    } catch (e) {
      console.error(e);
      setError(
        e?.response?.data?.message || e?.message || "Analysis request failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="max-w-3xl mx-auto text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-extrabold">
          Article Analyzer
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter a tariff article URL or paste tariff article text (or both), then click
          Analyze.
        </p>
      </header>

      <main className="max-w-3xl mx-auto space-y-4">
        <label className="block">
          <span className="text-sm font-medium">Article URL</span>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/tariff-article"
            className="mt-1 block w-full rounded-md border px-3 py-2 bg-card text-card-foreground"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium">Article text / Markdown</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste markdown or article text here..."
            rows={10}
            className="mt-1 block w-full rounded-md border px-3 py-2 bg-card text-card-foreground"
          />
        </label>

        {error && (
          <div className="text-sm text-red-600" role="alert">
            {error}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={handleAnalyze}
            disabled={!canAnalyze || loading}
            className={`inline-flex items-center px-4 py-2 rounded-md disabled:opacity-50 ${
              isDark ? "bg-primary text-black" : "bg-primary text-white"
            }`}
          >
            {loading ?
            <div className="flex items-center justify-center">
              <div>Analyzing...</div>
              <Spinner />
            </div> : "Analyze"}
          </button>

          <button
            type="button"
            onClick={() => {
              setUrl("");
              setText("");
              setResult(null);
              setError("");
            }}
            className="inline-flex items-center px-3 py-2 rounded-md border"
          >
            Reset
          </button>
        </div>

        {/* Results */}
        {result && (
          <section className="mt-6 bg-card text-card-foreground rounded-md border p-4">
            <h3 className="mt-4 font-semibold">Full model output</h3>
            <div className="prose max-w-none">
              <ReactMarkdown 
                components={{
                  ul: ({children}) => <ul className="list-disc ml-6 space-y-2">{children}</ul>,
                  // Ensure paragraphs have proper spacing
                  p: ({children}) => <p className="mb-4">{children}</p>,
                }}
            >
                {result}
              </ReactMarkdown>
            </div>

            {/* Fallback raw JSON */}
            {!result && (
              <pre className="mt-2 text-sm overflow-x-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
