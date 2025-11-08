import React, { useState, useEffect } from "react";
import { postAnalyzable } from "@/api/axiosClient";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTheme } from "@/components/theme-provider";

export default function Analyzer() {
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

  const [contentVisible, setContentVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setContentVisible(true), 500);
    return () => clearTimeout(t);
  }, []);

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
    <div className="relative min-h-screen overflow-hidden bg-transparent">
      {/* background barn video */}
      <div className="fixed inset-0 z-10 pointer-events-none">
        <video
          autoPlay
          loop
          muted
          playsInline
          key={isDark ? "dark-video" : "light-video"} // ensures React reloads video when theme changes
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-1000 ${contentVisible ? "blur-sm scale-105" : "blur-0 scale-100"
            }`}
        >
          <source
            src={isDark ? "/Barn_Night.mp4" : "/Barn_Animation.mp4"}
            type="video/mp4"
          />
        </video>
        <div
          className={`absolute inset-0 transition-opacity duration-1000 ${contentVisible ? (isDark ? "bg-black/70" : "bg-black/40") : "bg-black/30"
            }`}
        />
      </div>

      {/* Foreground card */}
      <div className="relative z-10">
        <div className="mx-auto max-w-6xl px-4 py-10">
          <div className="rounded-2xl border border-border bg-card text-card-foreground shadow-xl">
            {/* header bar */}
            <div className="rounded-t-2xl border-b border-border px-6 py-6 bg-emerald-50 dark:bg-emerald-900/20">
              <h1 className="text-xl md:text-2xl font-bold">Article Analyzer</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Enter a tariff article URL or paste tariff article text (or both), then click Analyze.
              </p>
            </div>

            {/* body */}
            <div className="px-4 md:px-6 py-6">
              <div className="mb-4 rounded-xl border border-border bg-card p-4">
                <label className="block">
                  <span className="text-sm font-medium">Article URL</span>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/tariff-article"
                    className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </label>

                <label className="mt-4 block">
                  <span className="text-sm font-medium">Article text / Markdown</span>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste markdown or article text here..."
                    rows={10}
                    className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </label>

                {error && (
                  <div className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
                    {error}
                  </div>
                )}

                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={handleAnalyze}
                    disabled={!canAnalyze || loading}
                    className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                  >
                    {loading ? "Analyzing…" : "Analyze"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setUrl("");
                      setText("");
                      setResult(null);
                      setError("");
                    }}
                    className="inline-flex items-center rounded-md border border-input bg-background px-3 py-2 text-foreground hover:bg-muted"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {result ? (
                <div className="rounded-xl border border-border bg-card p-4">
                  <h3 className="mb-2 font-semibold">Full model output</h3>
                  <div className="prose max-w-none dark:prose-invert">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        ul: ({ children }) => (
                          <ul className="ml-6 list-disc space-y-2">{children}</ul>
                        ),
                        p: ({ children }) => <p className="mb-4">{children}</p>,
                      }}
                    >
                      {result}
                    </ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div className="mt-4 rounded-xl border border-border bg-muted p-6 text-sm text-muted-foreground">
                  Paste content or a URL above, then click Analyze.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
