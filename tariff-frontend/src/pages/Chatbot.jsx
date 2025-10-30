import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

// Connect to your MCP-client server
const socket = io('http://127.0.0.1:8001');
// A unique ID for this chat session, you can make this more robust
const CHAT_THREAD_ID = 'user_session_123'; 

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
        if (lastMessage && lastMessage.sender === 'ai') {
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
      setIsAiTyping(false);
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
    socket.emit('chat_message', {
      message: currentInput,
      thread_id: CHAT_THREAD_ID, // Send the thread_id
    });
    
    setCurrentInput('');
    setIsAiTyping(true); // Show AI is "typing"
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <div style={{ border: '1px solid #ccc', height: '400px', overflowY: 'scroll', padding: '10px', marginBottom: '10px' }}>
        {messages.map((msg) => (
          <div key={msg.id} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <span style={{
              background: msg.sender === 'user' ? '#dcf8c6' : '#f1f0f0',
              padding: '8px 12px',
              borderRadius: '10px',
              display: 'inline-block',
            }}>
              {msg.text}
            </span>
          </div>
        ))}
        {isAiTyping && <div style={{ textAlign: 'left', color: '#888' }}>Jarvis is typing...</div>}
      </div>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          value={currentInput}
          onChange={(e) => setCurrentInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          style={{ flex: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button
          onClick={handleSend}
          style={{ padding: '10px', marginLeft: '5px', borderRadius: '5px', border: 'none', background: '#007bff', color: 'white' }}
        >
          Send
        </button>
      </div>
      <p>Connection status: {isConnected ? 'Connected' : 'Disconnected'}</p>
    </div>
  );
}

export default Chatbot;