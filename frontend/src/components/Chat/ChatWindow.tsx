import React, { useRef, useEffect, useState } from 'react';
import type { Message } from '../../types';
import { Send, Bot, User, Brain, Sparkles } from 'lucide-react';

interface ChatWindowProps {
    messages: Message[];
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages, onSendMessage, isLoading }) => {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput('');
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <header className="px-6 py-4 border-b border-border flex items-center justify-between glass sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center border border-primary/20">
                            <Sparkles className="w-5 h-5 text-primary" />
                        </div>
                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-background"></div>
                    </div>
                    <div>
                        <h1 className="font-semibold text-lg leading-none">Memory-Chat AI</h1>
                        <p className="text-sm text-muted-foreground mt-1">Smarter with every session</p>
                    </div>
                </div>
            </header>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-8 space-y-6 scroll-smooth">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto space-y-4">
                        <div className="w-16 h-16 bg-primary/5 rounded-2xl flex items-center justify-center border border-primary/10 mb-2">
                            <Brain className="w-8 h-8 text-primary" />
                        </div>
                        <h2 className="text-xl font-semibold italic text-primary/80">"How can I help you architect your next breakthrough?"</h2>
                        <p className="text-muted-foreground">My memory system is ready to provide hyper-personalized assistance based on our previous interactions.</p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1 ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-secondary border border-border'
                                }`}>
                                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5 text-primary" />}
                            </div>
                            <div className={`p-4 rounded-2xl ${msg.role === 'user'
                                ? 'bg-primary text-primary-foreground rounded-tr-none'
                                : 'bg-accent/40 text-foreground border border-border/50 rounded-tl-none'
                                }`}>
                                <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{msg.content}</p>
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="flex gap-3 max-w-[85%]">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-secondary border border-border mt-1">
                                <Bot className="w-5 h-5 text-primary animate-pulse" />
                            </div>
                            <div className="bg-accent/40 p-4 rounded-2xl rounded-tl-none border border-border/50 flex gap-1">
                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce"></span>
                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="p-6 pt-0">
                <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isLoading}
                        placeholder="Tell me about your project or preferences..."
                        className="w-full bg-secondary/30 border border-border rounded-2xl py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-muted-foreground disabled:opacity-50"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 top-2 p-2.5 bg-primary text-primary-foreground rounded-xl transition-all hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
                <p className="text-[10px] text-center text-muted-foreground mt-4 uppercase tracking-[0.2em] opacity-50">
                    Powered by safeqa observability system
                </p>
            </div>
        </div>
    );
};

export default ChatWindow;
