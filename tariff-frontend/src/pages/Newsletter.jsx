import React, { useEffect, useState } from 'react';
import { getNewsletter, getMailingList, saveMailingList, sendNewsletter } from "@/api/axiosClient";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, X, CheckCircle2, Edit } from "lucide-react";
import { Badge } from "@/components/ui/badge";

// --- This function is unchanged ---
function splitIntoItems(md) {
  if (!md) return [];
  // Split by horizontal rules or ## headers
  const pattern = /\[[\s]*!\[.*\n#+.*\n.*ago\n/g
  const items = md.match(pattern)
  return items;
}

// --- Helper to validate emails ---
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const isValidEmail = (email) => emailRegex.test(email);

function Newsletter() {
  const [grid, setGrid] = useState(null);
  const [list, setList] = useState(null);
  const [rawMarkdown, setRawMarkdown] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- State for mailing list and sending ---
  const [mailingList, setMailingList] = useState([]);
  const [currentEmailInput, setCurrentEmailInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [sendResult, setSendResult] = useState(null); // For send action
  const [saveResult, setSaveResult] = useState(null); // For save action
  const [isEditingList, setIsEditingList] = useState(false); // <-- NEW: To hide panel

  // --- Fetch both newsletter and mailing list ---
  useEffect(() => {
    let mounted = true;
    setLoading(true);

    const fetchNewsletter = getNewsletter()
      .then((res) => {
        if (!mounted) return;
        const md = res.data.markdown;
        setRawMarkdown(md);
        const newsItems = splitIntoItems(md);
        setGrid(newsItems.slice(0, 6));
        setList(newsItems.slice(6));
      })
      .catch((err) => {
        if (!mounted) return;
        console.error('Failed to load newsletter:', err);
        setError(err); // Only set main error for newsletter load fail
      });

    const fetchMailingList = getMailingList()
      .then(res => {
        if (!mounted) return;
        // axios wraps the response in a .data object
        if (res.data.recipients && Array.isArray(res.data.recipients)) {
          setMailingList(res.data.recipients);
        }
      })
      .catch(err => {
        if (!mounted) return;
        console.error('Failed to load mailing list:', err);
      });

    Promise.all([fetchNewsletter, fetchMailingList])
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // --- Logic to add emails from input ---
  const addEmailsToList = (emailString) => {
    const newEmails = emailString
      .split(/[\s,;]+/) // This already handles space, comma, semicolon, and newlines
      .map(email => email.trim())
      .filter(email => email && isValidEmail(email));
    
    if (newEmails.length > 0) {
      setMailingList(prevList => {
        const combined = [...prevList, ...newEmails];
        return [...new Set(combined)]; // Remove duplicates
      });
    }
  };

  const handleEmailInputKeyDown = (e) => {
    if (['Enter', ' ', ',', ';'].includes(e.key)) {
      e.preventDefault();
      addEmailsToList(currentEmailInput);
      setCurrentEmailInput("");
    }
  };

  const handleEmailInputPaste = (e) => {
    e.preventDefault();
    const pastedText = e.clipboardData.getData('text');
    addEmailsToList(pastedText);
    setCurrentEmailInput(""); // Clear input after paste
  };

  const removeEmail = (emailToRemove) => {
    setMailingList(prevList => prevList.filter(email => email !== emailToRemove));
  };

  // --- Handler for saving the mailing list ---
  const handleSaveList = async () => {
    setIsSaving(true);
    setSaveResult(null);
    let success = false;
    try {
      const res = await saveMailingList(mailingList);
      const result = res.data; // axios wraps response in .data

      if (result.status !== 'success') throw new Error(result.message || "Failed to save.");
      
      setSaveResult({ status: 'success', message: 'Mailing list saved!' });
      success = true;
    } catch (err) {
      // --- Axios error handling ---
      const message = err.response?.data?.detail || err.message || "Failed to save.";
      setSaveResult({ status: 'error', message: message });
      // --- END REFACTOR ---
    } finally {
      setIsSaving(false);
      if (success) {
        setTimeout(() => setSaveResult(null), 3000);
      }
    }
  };


  // --- Handler for sending the newsletter  ---
  const handleSendNewsletter = async () => {
    setIsSending(true);
    setSendResult(null);
    
    if (!rawMarkdown) {
      setSendResult({ status: 'error', message: 'Newsletter content is not loaded.' });
      setIsSending(false);
      return;
    }
    
    if (mailingList.length === 0) {
      setSendResult({ status: 'error', message: 'Mailing list is empty. Please add recipients first.' });
      setIsEditingList(true); // Open the editor
      setIsSending(false);
      return;
    }

    try {
      const res = await sendNewsletter(rawMarkdown);
      const result = res.data; // axios wraps response in .data

      if (result.status !== 'complete') throw new Error(result.detail || "An unknown error occurred.");

      setSendResult({ 
        status: 'success', 
        message: `Newsletter dispatch complete! Sent: ${result.total_sent}, Failed: ${result.total_failed}.` 
      });

    } catch (err) {
      console.error("Failed to send newsletter:", err);
      // --- Axios error handling ---
      const message = err.response?.data?.detail || err.message || "Failed to connect to the server.";
      setSendResult({ status: 'error', message: message });
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
          Newsletter Admin
        </h1>
        <p className="mt-3 text-lg text-muted-foreground max-w-2xl mx-auto dark:text-gray-300">
          Curated news, analyses, and mailing list management.
        </p>
      </header>
      
      <div className="max-w-2xl mx-auto bg-card text-card-foreground p-6 rounded-lg shadow-md border border-border mb-12">
        <h2 className="text-xl font-semibold mb-4">Send Newsletter Digest</h2>
        <div className="space-y-4">
          
          {/* --- Always Visible Send/Edit Buttons --- */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button 
              onClick={handleSendNewsletter} 
              disabled={isSending || mailingList.length === 0} 
              className="flex-1"
            >
              {isSending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                `Send to ${mailingList.length} ${mailingList.length === 1 ? 'User' : 'Users'}`
              )}
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setIsEditingList(prev => !prev)} 
              className="flex-1"
            >
              <Edit className="mr-2 h-4 w-4" />
              {isEditingList ? "Hide Editor" : "Edit Mailing List"}
            </Button>
          </div>

          {/* --- Send Result Alert --- */}
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

          {/* --- Collapsible Panel --- */}
          {isEditingList && (
            <div className="border-t border-border pt-6 mt-6 space-y-4">
              <h3 className="text-lg font-semibold text-muted-foreground">Manage Recipients</h3>
              
              {/* --- Email Tags Display --- */}
              <div className="p-3 border border-border rounded-md min-h-24 bg-background/50 flex flex-wrap gap-2">
                {mailingList.length === 0 ? (
                  <span className="text-sm text-muted-foreground p-2">No emails in list.</span>
                ) : (
                  mailingList.map(email => (
                    <Badge key={email} variant="secondary" className="text-sm py-1 px-2">
                      {email}
                      <button 
                        onClick={() => removeEmail(email)} 
                        className="ml-1.5 rounded-full hover:bg-muted-foreground/30 p-0.5"
                        aria-label={`Remove ${email}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))
                )}
              </div>

              {/* --- Email Input --- */}
              <div>
                <Label htmlFor="mailing-list-input">Add Emails</Label>
                <Input
                  id="mailing-list-input"
                  placeholder="Paste, or type (use enter, space, comma, or semicolon)"
                  value={currentEmailInput}
                  onChange={(e) => setCurrentEmailInput(e.target.value)}
                  onKeyDown={handleEmailInputKeyDown}
                  onPaste={handleEmailInputPaste}
                  className="mt-1"
                  disabled={isSaving}
                />
              </div>

              {/* --- Save Result Alert --- */}
              {saveResult && (
                <Alert variant={saveResult.status === 'error' ? 'destructive' : 'default'} className={saveResult.status === 'success' ? 'bg-green-50 border-green-200 text-green-800' : ''}>
                  {saveResult.status === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-Example 2:4" />}
                  <AlertDescription>
                    {saveResult.message}
                  </AlertDescription>
                </Alert>
              )}

              {/* --- Save Button --- */}
              <Button onClick={handleSaveList} disabled={isSaving} className="w-full">
                {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Save List"}
              </Button>
            </div>
          )}
        </div>
      </div>
      {/* --- End of MODIFIED UI --- */}


      {/* --- Newsletter Content Display (Unchanged) --- */}
      <h2 className="text-3xl font-bold text-center mb-10">Newsletter Preview</h2>
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