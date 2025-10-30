import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import Markdown from 'markdown-to-jsx'; // <-- 1. Import the new library

// Connect to your MCP-client server
const socket = io('http://127.0.0.1:8001'); //
// A unique ID for this chat session, you can make this more robust
const CHAT_THREAD_ID = 'user_session_123'; //

function Chatbot() {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [messages, setMessages] = useState([]); // List of all chat messages
  const [currentInput, setCurrentInput] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);

  useEffect(() => {
    function onConnect() {
      console.log('Connected to chatbot server!');
      setIsConnected(true);
    }

    function onDisconnect() {
      console.log('Disconnected from chatbot server.');
      setIsConnected(false);
    }

    // This listens for the 'ai_response' event from your server
    function onAiResponse(data) {
      const aiChunk = data.chunk;
      
      setMessages((prevMessages) => {
        const lastMessage = prevMessages[prevMessages.length - 1];
        
        // If the last message was from the AI, append to it
        if (lastMessage && lastMessage.sender === 'ai') { //
          return [
            ...prevMessages.slice(0, -1),
            { ...lastMessage, text: lastMessage.text + aiChunk },
          ];
        } else {
          // Otherwise, create a new AI message
          setIsAiTyping(true);
          return [
            ...prevMessages,
            { id: Date.now(), text: aiChunk, sender: 'ai' },
          ];
        }
      });
    }

    // This listens for the end-of-stream signal
    function onAiResponseEnd() {
      setIsAiTyping(false); //
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('ai_response', onAiResponse);
    socket.on('ai_response_end', onAiResponseEnd);

    // Clean up listeners on component unmount
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('ai_response', onAiResponse);
      socket.off('ai_response_end', onAiResponseEnd);
    };
  }, []);

  const handleSend = () => {
    if (!currentInput.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: currentInput,
      sender: 'user',
    };
    
    // Add user message to the chat
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    
    // Send the message to the server
    socket.emit('chat_message', { //
      message: currentInput,
      thread_id: CHAT_THREAD_ID, // Send the thread_id
    });
    
    setCurrentInput('');
    setIsAiTyping(true); // Show AI is "typing"
  };

  return (
    <div className="p-5 font-sans">
      <div className="border border-border h-96 overflow-y-auto p-2.5 mb-2.5 rounded-md">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.sender === 'user' ? 'text-right my-1.5' : 'text-left my-1.5'}>
            <span className={`
              py-2 px-3 rounded-lg inline-block text-left
              ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}
            `}>
              {/* --- 2. This is the new part --- */}
              {msg.sender === 'user' ? (
                msg.text // Keep user text plain
              ) : (
                // Render AI text with Markdown
                // We add 'prose' classes for nice typography
                <div className="prose dark:prose-invert prose-sm break-words">
                  <Markdown
                    options={{
                      // This forces all links to open in a new tab
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
              {/* --- End of new part --- */}
            </span>
          </div>
        ))}
        {isAiTyping && <div className="text-left text-muted-foreground">Jarvis is typing...</div>}
      </div>
      <div className="flex">
        <input
          type="text"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          style={{ flex: 1 }}
        />
        <button
          onClick={handleSend}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 ml-1.5"
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