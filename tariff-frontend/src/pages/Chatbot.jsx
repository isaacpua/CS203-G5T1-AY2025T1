import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import Markdown from 'markdown-to-jsx';

// Connect to your MCP-client server
const socket = io('http://127.0.0.1:8001');

// Helper function to generate unique thread IDs
const generateThreadId = () => `user_session_${Date.now()}_${Math.random().toString(36).substring(7)}`;

// --- NEW: PlusIcon component for the upload button ---
const PlusIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className="w-5 h-5" // Adjusted size
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);


function Chatbot() {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  const [threadId, setThreadId] = useState(generateThreadId());

  useEffect(() => {
    function onConnect() {
      console.log('Connected to chatbot server!');
      setIsConnected(true);
    }

    function onDisconnect() {
      console.log('Disconnected from chatbot server.');
      setIsConnected(false);
    }

    function onAiResponse(data) {
      const aiChunk = data.chunk;
      
      setMessages((prevMessages) => {
        const lastMessage = prevMessages[prevMessages.length - 1];
        
        if (lastMessage && lastMessage.sender === 'ai') {
          return [
            ...prevMessages.slice(0, -1),
            { ...lastMessage, text: lastMessage.text + aiChunk },
          ];
        } else {
          setIsAiTyping(true);
          return [
            ...prevMessages,
            { id: Date.now(), text: aiChunk, sender: 'ai' },
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

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('ai_response', onAiResponse);
      socket.off('ai_response_end', onAiResponseEnd);
    };
  }, []);

  // Read file as Base64 data URL
  const readFileAsBase64 = (file) => {
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
        reject(error);
      };
      reader.readAsDataURL(file); 
    });
  };

  const handleSend = async () => {
    if (!currentInput.trim() && !selectedFile) return;

    const userMessageText = currentInput || (selectedFile ? `File uploaded: ${selectedFile.name}` : "Empty message");

    const userMessage = {
      id: Date.now(),
      text: userMessageText,
      sender: 'user',
    };
    
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    
    let fileBase64 = null;
    let fileName = null;

    if (selectedFile) {
      try {
        fileBase64 = await readFileAsBase64(selectedFile);
        fileName = selectedFile.name;
      } catch (e) {
        console.error("Error reading file:", e);
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
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
    setIsAiTyping(true);
  };
  
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      // Update placeholder or input to show file name
      if (!currentInput.trim()) {
        setCurrentInput(`Analyzing: ${file.name}`);
      }
    }
  };

  const handleNewChat = () => {
    console.log("Starting new chat session...");
    setMessages([]);
    setCurrentInput("");
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
    setIsAiTyping(false);
    
    const newThreadId = generateThreadId();
    setThreadId(newThreadId); 
    console.log("New thread ID:", newThreadId);
  };

  return (
    <div className="p-5 font-sans">
      
      {/* --- NEW: "New Chat" button moved to top right --- */}
      <div className="flex justify-end mb-2">
        <button
          onClick={handleNewChat}
          title="Start a new chat (clears server memory)"
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-secondary text-secondary-foreground hover:bg-secondary/90 h-9 px-3" // Made slightly smaller
        >
          New Chat
        </button>
      </div>

      {/* Message Area (unchanged) */}
      <div className="border border-border h-96 overflow-y-auto p-2.5 mb-2.5 rounded-md">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.sender === 'user' ? 'text-right my-1.5' : 'text-left my-1.5'}>
            <span className={`
              py-2 px-3 rounded-lg inline-block text-left
              ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}
            `}>
              {msg.sender === 'user' ? (
                msg.text
              ) : (
                <div className="prose dark:prose-invert prose-sm break-words">
                  <Markdown
                    options={{
                      overrides: {
                        a: {
                          props: {
                            target: '_blank',
                            rel: 'noopener noreferrer',
                          },
                        },
                      },
                    }}
                  >
                    {msg.text}
                  </Markdown>
                </div>
              )}
            </span>
          </div>
        ))}
        {isAiTyping && <div className="text-left text-muted-foreground">Jarvis is typing...</div>}
      </div>
      
      {/* --- MODIFIED: Input Bar --- */}
      <div className="flex items-center gap-2"> {/* Use gap for spacing */}
        
        {/* --- NEW: Hidden file input --- */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".txt,.md,.csv,.json,.pdf,.docx,.xlsx,.pptx"
          className="hidden"
        />

        {/* --- NEW: Pretty "+" upload button --- */}
        <button
          onClick={() => fileInputRef.current.click()}
          title="Attach file"
          className="inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-secondary text-secondary-foreground hover:bg-secondary/90 h-10 w-10" // Rounded-full
        >
          <PlusIcon />
        </button>

        {/* Text Input */}
        <input
          type="text"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          style={{ flex: 1 }} // Use flex: 1 to fill space
          placeholder={selectedFile ? `File attached: ${selectedFile.name}` : "Type your message..."}
        />
        
        {/* Send Button */}
        <button
          onClick={handleSend}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          Send
        </button>

      </div>

      <p className="text-muted-foreground">
        Connection status: {isConnected ? <span className="text-green-500">Connected</span> : <span className="text-red-500">Disconnected</span>}
      </p>
    </div>
  );
}

export default Chatbot;