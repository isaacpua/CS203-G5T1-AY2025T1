import React, { useEffect, useState } from 'react';
import { getNewsletter } from "@/api/axiosClient";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// --- NEW IMPORTS ---
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea"; // Assuming you have this component
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, X } from "lucide-react";

// --- This function is unchanged ---
function splitIntoItems(md) {
  if (!md) return [];
  // Split by horizontal rules or ## headers
  const pattern = /\[[\s]*!\[.*\n#+.*\n.*ago\n/g
  const items = md.match(pattern)
  return items;
}



function Newsletter() {
  const [grid, setGrid] = useState(null);
  const [list, setList] = useState(null);
  const [rawMarkdown, setRawMarkdown] = useState(""); // <-- NEW: Store raw markdown
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- NEW: State for the sending feature ---
  const [mailingList, setMailingList] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendResult, setSendResult] = useState(null); // { status: 'success'/'error', message: '...' }

  // --- This useEffect is updated to store raw markdown ---
  useEffect(() => {
    let mounted = true;
    setLoading(true);

    getNewsletter()
      .then((res) => {
        if (!mounted) return;
        const md = res.data.markdown;
        
        setRawMarkdown(md); // <-- NEW: Store the raw markdown
        
        const newsItems = splitIntoItems(md);
        console.log("Number of news items: " + newsItems.length)
        for (const item of newsItems) {
          console.log("New item!")
          console.log(item)
        }
        setGrid(newsItems.slice(0, 6)); // First 6 items for the grid
        setList(newsItems.slice(6)); // Remaining items
      })
      .catch((err) => {
        if (!mounted) return;
        console.error('Failed to load newsletter:', err);
        setError(err);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // --- NEW: Handler for calling the MCP-Gateway endpoint ---
  const handleSendNewsletter = async () => {
    setIsSending(true);
    setSendResult(null);

    // Basic email validation and list parsing
    const recipients = mailingList
      .split(/[\n,;]+/) // Split by newline, comma, or semicolon
      .map(email => email.trim())
      .filter(email => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)); // Basic email regex

    if (recipients.length === 0) {
      setSendResult({ status: 'error', message: 'No valid email addresses provided.' });
      setIsSending(false);
      return;
    }
    
    if (!rawMarkdown) {
      setSendResult({ status: 'error', message: 'Newsletter content is not loaded.' });
      setIsSending(false);
      return;
    }

    try {
      // Call the new endpoint on your MCP-Gateway (running on port 8090)
      //
      // This matches the route defined in routes.py
      //
      const response = await fetch("http://127.0.0.1:8090/mcp/api/v1/newsletter/send", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // If your gateway is protected, add your auth header
          // 'Authorization': `Bearer ${localStorage.getItem("accessToken")}`
        },
        body: JSON.stringify({
          markdown_content: rawMarkdown,
          recipients: recipients
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "An unknown error occurred.");
      }

      setSendResult({ 
        status: 'success', 
        message: `Newsletter dispatch complete! Sent: ${result.total_sent}, Failed: ${result.total_failed}.` 
      });
      setMailingList(""); // Clear list on success

    } catch (err) {
      console.error("Failed to send newsletter:", err);
      setSendResult({ status: 'error', message: err.message || "Failed to connect to the server." });
    } finally {
      setIsSending(false);
    }
  };


  if (loading) return <div>Loading newsletter...</div>;
  if (error) return <div>Error loading newsletter.</div>;



  return (
    <div className="container mx-auto px-4 py-8">
      <header className="max-w-4xl mx-auto text-center mb-10">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-sky-600 to-indigo-600">
          Tariff Newsletter
        </h1>
        <p className="mt-3 text-lg text-muted-foreground max-w-2xl mx-auto dark:text-gray-300">
          Curated news and analyses
        </p>
      </header>
      
      {/* --- NEW: Sending Feature UI --- */}
      <div className="max-w-2xl mx-auto bg-card text-card-foreground p-6 rounded-lg shadow-md border border-border mb-12">
        <h2 className="text-xl font-semibold mb-4">Send Newsletter Digest</h2>
        <div className="space-y-4">
          <div>
            <Label htmlFor="mailing-list">Mailing List</Label>
            <Textarea
              id="mailing-list"
              placeholder="Paste email addresses, separated by commas, semicolons, or new lines."
              value={mailingList}
              onChange={(e) => setMailingList(e.target.value)}
              className="mt-1"
              rows={4}
              disabled={isSending}
            />
          </div>

          {sendResult && (
            <Alert variant={sendResult.status === 'error' ? 'destructive' : 'default'} className={sendResult.status === 'success' ? 'bg-green-50 border-green-200 text-green-800' : ''}>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex justify-between items-center">
                <span>{sendResult.message}</span>
                <Button variant="ghost" size="sm" className="h-auto p-1" onClick={() => setSendResult(null)}>
                  <X className="h-3 w-3" />
                </Button>
              </AlertDescription>
            </Alert>
          )}

          <Button onClick={handleSendNewsletter} disabled={isSending || !mailingList || !rawMarkdown} className="w-full">
            {isSending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              "Send to Mailing List"
            )}
          </Button>
        </div>
      </div>
      {/* --- End of NEW UI --- */}


      {/* Grid Layout for first 6 items */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {grid?.map((item, idx) => (
          <article 
            key={idx} 
            className="bg-card text-card-foreground rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow border border-border"
          >
            <div className="p-6">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    img: ({node, ...props}) => (
                      <img 
                        {...props} 
                        className="w-full h-48 object-cover rounded-md mb-4 border border-border" 
                        loading="lazy"
                      />
                    ),
                    h1: ({node, ...props}) => (
                      <h1 {...props} className="text-xl font-bold mb-3 text-foreground" />
                    ),
                    h2: ({node, ...props}) => (
                      <h2 {...props} className="text-lg font-semibold mb-2 text-foreground" />
                    ),
                    p: ({node, ...props}) => (
                      <p {...props} className="mb-3 line-clamp-3 text-muted-foreground" />
                    ),
                    a: ({node, ...props}) => (
                      <a {...props} className="text-primary hover:text-primary/80 transition-colors" />
                    ),
                  }}
                >
                  {item}
                </ReactMarkdown>
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* List Layout for remaining items */}
      <div className="space-y-8">
        {list?.map((item, idx) => (
          <article 
            key={idx} 
            className="bg-card text-card-foreground rounded-lg shadow-sm p-6 border border-border"
          >
            <div className="prose max-w-none dark:prose-invert">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  img: ({node, ...props}) => (
                    <img 
                      {...props} 
                      className="max-w-full h-auto my-4 rounded-lg shadow-md border border-border"
                      loading="lazy"
                    />
                  ),
                  h1: ({node, ...props}) => (
                    <h1 {...props} className="text-xl font-bold mb-3 text-foreground" />
                  ),
                  h2: ({node, ...props}) => (
                    <h2 {...props} className="text-lg font-semibold mb-2 text-foreground" />
                  ),
                  p: ({node, ...props}) => (
                    <p {...props} className="mb-3 text-muted-foreground" />
                  ),
                  a: ({node, ...props}) => (
                    <a {...props} className="text-primary hover:text-primary/80 transition-colors" />
                  ),
                }}
              >
                {item}
              </ReactMarkdown>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export default Newsletter;