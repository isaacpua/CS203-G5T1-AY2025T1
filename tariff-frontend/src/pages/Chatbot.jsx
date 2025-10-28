import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function ChatbotPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Chatbot Interface</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Chatbot UI will go here.</p>
        {/* Add chat input, message display area etc. later */}
      </CardContent>
    </Card>
  );
}