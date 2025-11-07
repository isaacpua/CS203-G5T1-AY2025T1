import React, { useState, useEffect, useRef } from 'react'; // useRef is imported
import { io } from 'socket.io-client';
import Markdown from 'markdown-to-jsx';

// Connect to your MCP-client server
const socket = io('http://127.0.0.1:8001');

// Helper function to generate unique thread IDs
const generateThreadId = () => `user_session_${Date.now()}_${Math.random().toString(36).substring(7)}`;

// --- (All Icon components unchanged) ---
const SpinnerIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 animate-spin">
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </svg>
);
const XIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
  </svg>
);
const PlusIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);
const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 text-gray-400">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
  </svg>
);
const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
    <path fillRule="evenodd" d="M15.625 8.25a.75.75 0 0 1 .75.75v5.25a2.75 2.75 0 0 1-2.75 2.75H6.375a2.75 2.75 0 0 1-2.75-2.75V9a.75.75 0 0 1 1.5 0v5.25c0 .69.56 1.25 1.25 1.25h8.25c.69 0 1.25-.56 1.25-1.25V9a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
    <path fillRule="evenodd" d="M10 2a.75.75 0 0 1 .75.75v8.793l2.043-2.043a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L6.25 10.06a.75.75 0 1 1 1.06-1.06L9.35 11.043V2.75A.75.75 0 0 1 10 2Z" clipRule="evenodd" />
  </svg>
);

const ACCEPTED_FILE_TYPES = [
  ".txt", ".md", ".csv", ".json", ".pdf", ".docx", ".xlsx", ".pptx"
];

function Chatbot() {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  const [threadId, setThreadId] = useState(generateThreadId());
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [fileError, setFileError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    function onConnect() {
      console.log('Connected to chatbot server!');
      setIsConnected(true);
    }
    function onDisconnect() {
      console.log('Disconnected from chatbot server.');
      setIsConnected(false);
    }
    function onToolCall(data) {
      setIsAiTyping(true); 
      setMessages((prevMessages) => {
        const lastMessage = prevMessages[prevMessages.length - 1];
        if (lastMessage && lastMessage.type === 'tool_group') {
          if (!lastMessage.tools.find(t => t.name === data.tool_name)) {
            return [
              ...prevMessages.slice(0, -1),
              { 
                ...lastMessage, 
                tools: [...lastMessage.tools, { name: data.tool_name }]
              },
            ];
          }
          return prevMessages;
        } else {
          return [
            ...prevMessages,
            { 
              id: Date.now(), 
              sender: 'ai',
              type: 'tool_group', 
              tools: [{ name: data.tool_name }]
            },
          ];
        }
      });
    }
    function onAiResponse(data) {
      const aiChunk = data.chunk;
      setMessages((prevMessages) => {
        const lastMessage = prevMessages[prevMessages.length - 1];
        if (lastMessage && lastMessage.sender === 'ai' && lastMessage.type === 'ai_response') {
          return [
            ...prevMessages.slice(0, -1),
            { ...lastMessage, text: lastMessage.text + aiChunk },
          ];
        } else {
          setIsAiTyping(true);
          return [
            ...prevMessages,
            { 
              id: Date.now(), 
              text: aiChunk, 
              sender: 'ai', 
              type: 'ai_response'
            },
          ];
        }
      });
    }
    function onAiResponseEnd() {
      setIsAiTyping(false);
    }
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('ai_response', onAiResponse);
    socket.on('ai_response_end', onAiResponseEnd);
    socket.on('tool_call', onToolCall); 
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('ai_response', onAiResponse);
      socket.off('ai_response_end', onAiResponseEnd);
      socket.off('tool_call', onToolCall);
    };
  }, []);

  const readFileAsBase64 = (file) => {
    // ... (File reading logic unchanged) ...
    return new Promise((resolve, reject) => {
      if (!file) {
        resolve(null);
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = (error) => {
        console.error("FileReader error:", error);
        reject(new Error("Failed to read file. It may be too large or unreadable by the browser."));
      };
      reader.readAsDataURL(file); 
    });
  };

  const handleSend = async () => {
    // ... (handleSend logic unchanged) ...
    if ((!currentInput.trim() && !selectedFile) || isLoadingFile) return; 
    const userMessage = {
      id: Date.now(),
      text: currentInput.trim(), 
      fileName: selectedFile ? selectedFile.name : null, 
      sender: 'user',
      type: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    let fileBase64 = null;
    let fileName = null;
    if (selectedFile) {
      setIsLoadingFile(true); 
      setFileError(null);     
      try {
        fileBase64 = await readFileAsBase64(selectedFile);
        fileName = selectedFile.name; 
      } catch (e) {
        console.error("File read error:", e);
        setFileError(e.message || "Failed to read file.");
        setIsLoadingFile(false); 
        setMessages((prev) => prev.slice(0, -1)); 
        return; 
      }
    }
    socket.emit('chat_message', {
      message: currentInput, 
      thread_id: threadId,
      file_base64: fileBase64,
      file_name: fileName,
    });
    setCurrentInput('');
    setSelectedFile(null); 
    setIsLoadingFile(false); 
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
    setIsAiTyping(true); 
  };
  
  const handleFile = (files) => {
    // ... (unchanged) ...
    if (!files || files.length === 0) {
      return;
    }
    if (files.length > 1) {
      setFileError("Please upload only one file at a time.");
      return;
    }
    const file = files[0];
    const fileExtension = "." + file.name.split('.').pop().toLowerCase();
    if (ACCEPTED_FILE_TYPES.includes(fileExtension)) {
      setFileError(null);
      setSelectedFile(file);
    } else {
      setFileError(`Unsupported file type. Please upload one of: ${ACCEPTED_FILE_TYPES.join(', ')}`);
      setSelectedFile(null);
    }
  };

  const handleFileChange = (e) => {
    handleFile(e.target.files);
  };

  const handleNewChat = () => {
    console.log("Starting new chat session...");
    try {
      socket.emit("cancel_processing", { thread_id: threadId });
    } catch (e) {
      console.warn("Failed to emit cancel_processing:", e);
    }

    setMessages([]);
    setCurrentInput("");
    setSelectedFile(null);
    setFileError(null);
    setIsLoadingFile(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
    setIsAiTyping(false);
    const newThreadId = generateThreadId();
    setThreadId(newThreadId);
    console.log("New thread ID:", newThreadId);
  };

  const handleRemoveFile = () => {
    // ... (unchanged) ...
    setSelectedFile(null);
    setFileError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files);
  };

  const formatTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "";
    }
  };
  
  return (
    <div className="flex items-center justify-center p-6">
      <div 
        className="relative w-full max-w-3xl bg-card/80 dark:bg-card rounded-lg shadow-xl overflow-hidden ring-1 ring-border"
        onDragOver={handleDragOver}
      >
        
        {isDragging && (
          <div 
            className="absolute inset-0 bg-background/80 flex flex-col items-center justify-center z-10 border-4 border-dashed border-primary/50 rounded-lg"
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <UploadIcon />
            <p className="mt-2 text-lg font-medium">Drop file to attach</p>
          </div>
        )}

        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary/10 to-transparent border-b border-border">
          <div className="flex items-center gap-3">
            <img src="/eve-avatar.svg" alt="T.A.R.I.F.F" className="w-10 h-10 rounded-full object-cover" />
            <div>
              <div className="font-semibold text-sm">T.A.R.I.F.F</div>
              <div className="text-xs text-muted-foreground">AI Assistant</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleNewChat}
              title="Start a new chat (clears server memory)"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/90 h-8 px-3"
            >
              New Chat
            </button>
          </div>
        </div>

        <div className="h-[60vh] overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-transparent to-background">
          {messages.length === 0 && (
            <div className="text-center text-sm text-muted-foreground mt-8">No messages yet — say hello 👋</div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex items-end ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                {msg.sender !== 'user' && (
                <div className="flex-shrink-0 mr-3">
                  <img src="/eve-avatar.svg" alt="T.A.R.I.F.F" className="w-8 h-8 rounded-full object-cover" />
                </div>
              )}

              <div className={`max-w-[75%] ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                <div
                  className={`inline-block px-4 py-2 rounded-lg break-words ${
                    msg.sender === 'user'
                      ? 'bg-primary text-primary-foreground rounded-br-none'
                      : 'bg-white/95 dark:bg-muted text-foreground rounded-bl-none'
                  }`}
                >
                  {msg.type === 'user' ? (
                    <div className="flex flex-col items-end">
                      {msg.fileName && (
                        <div className="mb-1.5 flex items-center gap-2 py-1 px-2.5 rounded-lg bg-black/5">
                          <FileIcon />
                          <span className="text-sm font-medium">{msg.fileName}</span>
                        </div>
                      )}
                      {msg.text && <div>{msg.text}</div>}
                    </div>
                  ) : msg.type === 'tool_group' ? (
                    <div className="flex flex-col gap-2">
                      <div className="text-xs font-medium text-muted-foreground">Running tools...</div>
                      <div className="flex flex-wrap gap-2">
                        {msg.tools.map((tool, index) => (
                          <div key={index} className="flex items-center gap-1.5 bg-blue-100 text-blue-800 rounded-lg py-1 px-3 text-sm">
                            {tool.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="prose dark:prose-invert prose-sm wrap-break-word">
                      <Markdown options={{ overrides: { a: { props: { target: '_blank', rel: 'noopener noreferrer', className: 'text-blue-600 dark:text-blue-400' } } } }}>
                        {msg.text || ''}
                      </Markdown>
                    </div>
                  )}
                </div>

                <div className="text-[11px] text-muted-foreground mt-1">
                  {formatTime(msg.id)}
                </div>
              </div>
            </div>
          ))}

          {isAiTyping && (
            <div className="flex items-center gap-2">
              <img src="/eve-avatar.svg" alt="T.A.R.I.F.F" className="w-8 h-8 rounded-full object-cover" />
              <SpinnerIcon />
              <div className="inline-block px-4 py-2 rounded-lg bg-white/90 dark:bg-muted text-foreground">T.A.R.I.F.F is typing...</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="px-4 py-3 border-t border-border bg-card">
          {selectedFile && (
            <div className="mb-2 flex items-center gap-2">
              <div className="flex items-center gap-2 py-1 px-3 rounded-full bg-muted text-sm">
                <FileIcon />
                <span className="truncate max-w-[18rem]">{selectedFile.name}</span>
                <button onClick={handleRemoveFile} className="ml-2 p-1 rounded hover:bg-background/50">
                  <XIcon />
                </button>
              </div>
            </div>
          )}

          {fileError && (
            <div className="mb-2 text-red-600 text-sm">
              <strong>Error:</strong> {fileError}
            </div>
          )}

          <div className="flex items-center gap-2">
            <input type="file" ref={fileInputRef} onChange={handleFileChange} accept={ACCEPTED_FILE_TYPES.join(',')} className="hidden" disabled={isLoadingFile} />
            <button onClick={() => fileInputRef.current.click()} title="Attach file" className="inline-flex items-center justify-center rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/90 h-9 w-9">
              <PlusIcon />
            </button>
            <input
              type="text"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none"
              placeholder="Ask T.A.R.I.F.F anything..."
              disabled={isLoadingFile}
            />
            <button onClick={handleSend} className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4" disabled={isLoadingFile || isAiTyping}>
              Send
            </button>
          </div>

          <div className="mt-2 text-xs text-muted-foreground">Connection: {isConnected ? <span className="text-green-500">Connected</span> : <span className="text-red-500">Disconnected</span>}</div>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
