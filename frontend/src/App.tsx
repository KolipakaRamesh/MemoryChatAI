import React, { useState } from 'react';
import { Brain, User, Bot, Sparkles } from 'lucide-react';
import { chatApi } from './api/client';
import type { Message, ObservabilityData } from './types';
import ChatWindow from './components/Chat/ChatWindow';
import MemoryDashboard from './components/Dashboard/MemoryDashboard';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [observability, setObservability] = useState<ObservabilityData | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'memory'>('chat');

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const result = await chatApi.sendMessage(content, conversationId);

      const assistantMessage: Message = {
        id: result.message_id,
        role: 'assistant',
        content: result.response,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(result.conversation_id);
      setObservability(result.observability);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: Date.now().toString() + '_error',
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden text-foreground">
      {/* Sidebar */}
      <div className="w-16 flex flex-col items-center py-6 border-r border-border glass gap-8">
        <div className="p-2 bg-primary/10 rounded-xl">
          <Brain className="w-8 h-8 text-primary" />
        </div>
        <div className="flex-1 flex flex-col gap-4">
          <button
            onClick={() => setActiveTab('chat')}
            className={`p-3 rounded-xl transition-all ${activeTab === 'chat' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent text-muted-foreground'}`}
          >
            <Bot className="w-6 h-6" />
          </button>
          <button
            onClick={() => setActiveTab('memory')}
            className={`p-3 rounded-xl transition-all ${activeTab === 'memory' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent text-muted-foreground'}`}
          >
            <Sparkles className="w-6 h-6" />
          </button>
        </div>
        <div className="p-3 hover:bg-accent text-muted-foreground rounded-xl cursor-pointer">
          <User className="w-6 h-6" />
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        <div className={`flex-1 flex flex-col min-w-0 transition-all ${activeTab === 'chat' ? 'w-full' : 'w-0 hidden md:flex'}`}>
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>

        {/* Right Dashboard */}
        <div className={`w-full md:w-96 lg:w-[450px] border-l border-border bg-card/50 transition-all ${activeTab === 'memory' ? 'w-full' : 'hidden lg:block'}`}>
          <MemoryDashboard data={observability} />
        </div>
      </main>
    </div>
  );
};

export default App;
