import React, { useState } from 'react';
import type { ObservabilityData } from '../../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Database, Zap, Layers, MessageSquare, Activity, Cpu, BarChart3, User, X, ExternalLink, Sparkles } from 'lucide-react';

interface MemoryDashboardProps {
    data: ObservabilityData | null;
}

const MemoryDashboard: React.FC<MemoryDashboardProps> = ({ data }) => {
    const [selectedDetail, setSelectedDetail] = useState<{ title: string, content: any } | null>(null);

    if (!data) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-card/10">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center opacity-20 mb-4">
                    <Activity className="w-8 h-8" />
                </div>
                <h3 className="text-muted-foreground font-medium">Observability Engine Standby</h3>
                <p className="text-sm text-muted-foreground/60 mt-2">Send a message to visualize memory retrieval and token usage in real-time.</p>
            </div>
        );
    }

    const tokenData = Object.entries(data.token_usage.breakdown).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value
    })).filter(d => d.value > 0);

    const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#eab308'];

    return (
        <div className="h-full flex flex-col bg-card/50 relative overflow-hidden">
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 scrollbar-hide">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary" />
                        Memory Dashboard
                    </h2>
                    <div className="text-[10px] px-2 py-1 bg-primary/10 rounded-full text-primary font-mono uppercase tracking-wider">
                        Obs: {data.request_id.slice(0, 8)}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-2xl bg-secondary/30 border border-border/50">
                        <div className="flex items-center gap-2 text-muted-foreground mb-1">
                            <Zap className="w-3 h-3 text-yellow-500" />
                            <span className="text-[10px] font-bold uppercase tracking-tight">Tokens</span>
                        </div>
                        <div className="text-xl font-bold">{data.token_usage.total}</div>
                    </div>
                    <div className="p-3 rounded-2xl bg-secondary/30 border border-border/50">
                        <div className="flex items-center gap-2 text-muted-foreground mb-1">
                            <Cpu className="w-3 h-3 text-blue-500" />
                            <span className="text-[10px] font-bold uppercase tracking-tight">Cost</span>
                        </div>
                        <div className="text-xl font-bold">${data.token_usage.cost.toFixed(4)}</div>
                    </div>
                </div>

                {/* Token Usage Chart */}
                <div className="space-y-3">
                    <h3 className="text-[10px] font-bold text-muted-foreground flex items-center gap-2 uppercase tracking-widest pl-1">
                        <BarChart3 className="w-3 h-3" />
                        Token Breakdown
                    </h3>
                    <div className="h-[140px] w-full bg-secondary/10 rounded-2xl p-2 border border-border/20">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={tokenData} layout="vertical" margin={{ left: -20, right: 10 }}>
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }}
                                />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={12}>
                                    {tokenData.map((_entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Memory Systems */}
                <div className="space-y-3 pb-4">
                    <h3 className="text-[10px] font-bold text-muted-foreground flex items-center gap-2 uppercase tracking-widest pl-1">
                        <Database className="w-3 h-3" />
                        Memory Retrieval
                    </h3>

                    <div className="space-y-2">
                        {/* Long Term */}
                        <div
                            onClick={() => setSelectedDetail({ title: 'User Context Profile', content: data.long_term_memory })}
                            className="p-3 rounded-xl bg-accent/10 border border-border/30 hover:border-primary/40 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex gap-2">
                                    <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center">
                                        <User className="w-3 h-3 text-primary" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-semibold">User Context</h4>
                                        <p className="text-[10px] text-muted-foreground truncate">Preferences & History</p>
                                    </div>
                                </div>
                                <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-primary transition-colors mt-1" />
                            </div>
                            <div className="mt-2 flex flex-wrap gap-1">
                                {Object.entries(data.long_term_memory.preferences || {}).slice(0, 3).map(([key, value]) => (
                                    <span key={key} className="px-1.5 py-0.5 bg-background/50 border border-border/50 rounded-md text-[9px] text-muted-foreground whitespace-nowrap">
                                        {key.split('_')[0]}: {String(value)}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Recent Context */}
                        <div
                            onClick={() => setSelectedDetail({ title: 'Recent Conversation History', content: data.short_term_memory })}
                            className="p-3 rounded-xl bg-accent/10 border border-border/30 hover:border-blue-500/40 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex gap-2">
                                    <div className="w-6 h-6 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                        <MessageSquare className="w-3 h-3 text-blue-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-semibold">Recent Context</h4>
                                        <p className="text-[10px] text-muted-foreground">Last {data.short_term_memory.messages.length} messages</p>
                                    </div>
                                </div>
                                <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-blue-500 transition-colors mt-1" />
                            </div>
                        </div>

                        {/* Semantic Records */}
                        <div
                            onClick={() => setSelectedDetail({ title: 'Semantic Knowledge Retrieval', content: data.semantic_memory })}
                            className="p-3 rounded-xl bg-accent/10 border border-border/30 hover:border-pink-500/40 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex gap-2">
                                    <div className="w-6 h-6 rounded-lg bg-pink-500/10 flex items-center justify-center">
                                        <Layers className="w-3 h-3 text-pink-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-semibold">Semantic Records</h4>
                                        <p className="text-[10px] text-muted-foreground">Vector-based search</p>
                                    </div>
                                </div>
                                <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-pink-500 transition-colors mt-1" />
                            </div>
                            <div className="mt-2 text-[9px] text-muted-foreground font-mono bg-black/5 px-2 py-1 rounded">
                                {data.semantic_memory.relevant_memories.length > 0
                                    ? `Total: ${data.semantic_memory.relevant_memories.length} results`
                                    : "ChromaDB standby"}
                            </div>
                        </div>

                        {/* Feedback Memory */}
                        <div
                            onClick={() => setSelectedDetail({ title: 'Feedback & Learning', content: data.feedback_memory })}
                            className="p-3 rounded-xl bg-accent/10 border border-border/30 hover:border-amber-500/40 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex gap-2">
                                    <div className="w-6 h-6 rounded-lg bg-amber-500/10 flex items-center justify-center">
                                        <Sparkles className="w-3 h-3 text-amber-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-semibold">Feedback Memory</h4>
                                        <p className="text-[10px] text-muted-foreground">Learning from corrections</p>
                                    </div>
                                </div>
                                <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-amber-500 transition-colors mt-1" />
                            </div>
                            <div className="mt-2 text-[9px] text-muted-foreground font-mono bg-black/5 px-2 py-1 rounded">
                                {data.feedback_memory.corrections.length > 0
                                    ? `Active: ${data.feedback_memory.corrections.length} rules`
                                    : 'Use "Incorrect:" to seed'}
                            </div>
                        </div>

                        {/* Processing Trace */}
                        <div className="p-3 rounded-xl bg-secondary/10 border border-border/30">
                            <h4 className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
                                <Activity className="w-3 h-3" />
                                Processing Trace
                            </h4>
                            <div className="space-y-3 pb-1">
                                {data.request_trace.steps.map((step, i) => (
                                    <div key={i} className="relative pl-3 border-l border-border/50">
                                        <div className="absolute -left-[3.5px] top-1 w-1.5 h-1.5 rounded-full bg-primary/40"></div>
                                        <div className="flex justify-between items-center text-[10px]">
                                            <span className="font-medium">{step.name}</span>
                                            <span className="font-mono text-primary group-hover:font-bold">{step.latency_ms.toFixed(0)}ms</span>
                                        </div>
                                    </div>
                                ))}
                                <div className="flex justify-between pt-2 border-t border-border/30 text-[10px] font-bold">
                                    <span className="uppercase text-muted-foreground tracking-tighter">Total</span>
                                    <span className="text-primary font-mono">{data.request_trace.total_latency_ms.toFixed(0)}ms</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Detail Overlay */}
            {selectedDetail && (
                <div className="absolute inset-4 z-50 bg-background border border-border shadow-2xl rounded-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                    <div className="p-4 border-b border-border flex items-center justify-between bg-secondary/10">
                        <h4 className="text-sm font-bold truncate pr-4">{selectedDetail.title}</h4>
                        <button
                            onClick={() => setSelectedDetail(null)}
                            className="p-1.5 hover:bg-destructive/10 hover:text-destructive rounded-lg transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="flex-1 overflow-auto p-4 bg-black/[0.02]">
                        <pre className="text-[10px] font-mono whitespace-pre-wrap leading-relaxed text-muted-foreground">
                            {JSON.stringify(selectedDetail.content, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MemoryDashboard;
