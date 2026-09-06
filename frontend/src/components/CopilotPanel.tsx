import React, { useState } from 'react';
import { askCopilot } from '../api/client';
import { Send, Loader2, Lightbulb, Database, Quote } from 'lucide-react';

interface CopilotPanelProps {
    investigationId: string;
    context?: any;
}

export const CopilotPanel: React.FC<CopilotPanelProps> = ({ investigationId, context }) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<any[]>([]);

    const predefinedQuestions = [
        "What changed in the dataset?",
        "What should I investigate next?",
        "Are there any plausible hypotheses?",
        "Draft a query to check for duplicates."
    ];

    const handleSubmit = async (text: string) => {
        if (!text.trim()) return;
        
        setHistory(prev => [...prev, { role: 'user', content: text }]);
        setQuery('');
        setLoading(true);

        try {
            // Ideally we'd send context in askCopilot, but for now we just keep it simple
            const resp = await askCopilot(investigationId, text);
            setHistory(prev => [...prev, { role: 'copilot', content: resp }]);
        } catch (error) {
            console.error(error);
            setHistory(prev => [...prev, { role: 'copilot', error: true, content: "Copilot temporarily unavailable. Please try again." }]);
        } finally {
            setLoading(false);
        }
    };
        <div className="flex flex-col h-full bg-slate-50 border-l border-slate-200 w-96 shadow-xl shrink-0">
            <div className="p-4 bg-slate-800 text-white flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-300" />
                <h2 className="font-semibold">DataForge Copilot</h2>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {history.length === 0 && (
                    <div className="text-sm text-slate-500 space-y-4">
                        <p>Ask a question to investigate this issue using the deterministic evidence graph.</p>
                        <div className="flex flex-col gap-2">
                            {predefinedQuestions.map((q, i) => (
                                <button 
                                    key={i} 
                                    onClick={() => handleSubmit(q)}
                                    className="text-left p-2 rounded border border-slate-200 hover:bg-slate-100 transition-colors text-slate-700 shadow-sm"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {history.map((msg, i) => (
                    <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        {msg.role === 'user' ? (
                            <div className="bg-blue-600 text-white rounded-lg rounded-tr-none px-4 py-2 max-w-[90%] text-sm shadow">
                                {msg.content}
                            </div>
                        ) : (
                            <div className="bg-white border border-slate-200 rounded-lg rounded-tl-none p-4 max-w-full text-sm shadow-sm w-full space-y-4">
                                {msg.error ? (
                                    <div className="text-red-500">Error: {msg.error}</div>
                                ) : (
                                    <>
                                        <div className="text-slate-800 leading-relaxed whitespace-pre-wrap">
                                            {msg.content.answer}
                                        </div>
                                        
                                        {msg.content.hypotheses && msg.content.hypotheses.length > 0 && (
                                            <div className="space-y-2 mt-4">
                                                <div className="font-semibold text-slate-700 flex items-center gap-1">
                                                    <Lightbulb className="w-4 h-4 text-amber-500"/> Suggested Hypotheses
                                                </div>
                                                {msg.content.hypotheses.map((h: any, j: number) => (
                                                    <div key={j} className="bg-amber-50 p-2 rounded border border-amber-100 text-amber-900 text-xs">
                                                        {h.description}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {msg.content.experiments && msg.content.experiments.length > 0 && (
                                            <div className="space-y-2 mt-4">
                                                <div className="font-semibold text-slate-700 flex items-center gap-1">
                                                    <Database className="w-4 h-4 text-blue-500"/> Experiments
                                                </div>
                                                {msg.content.experiments.map((exp: any, j: number) => (
                                                    <div key={j} className="bg-slate-900 rounded overflow-hidden">
                                                        <div className="bg-blue-900 text-blue-100 text-xs px-2 py-1 font-semibold tracking-wider flex justify-between">
                                                            <span>SQL</span>
                                                            <span className="text-yellow-300 uppercase">Draft — Requires Review</span>
                                                        </div>
                                                        <pre className="p-3 text-emerald-400 text-xs overflow-x-auto font-mono">
                                                            {exp.sql_draft}
                                                        </pre>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {msg.content.citations && msg.content.citations.length > 0 && (
                                            <div className="mt-4 pt-4 border-t border-slate-100 space-y-1">
                                                <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider flex items-center gap-1">
                                                    <Quote className="w-3 h-3" /> Evidence Sources
                                                </div>
                                                {msg.content.citations.map((c: any, j: number) => (
                                                    <div key={j} className="text-xs text-slate-500 flex gap-2">
                                                        <span className="bg-slate-100 text-slate-600 px-1 rounded">[{c.citation_id}]</span>
                                                        <span>{c.description}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex items-center gap-2 text-slate-400 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" /> Copilot is thinking...
                    </div>
                )}
            </div>
            
            <div className="p-4 border-t border-slate-200 bg-white">
                <form 
                    className="flex gap-2"
                    onSubmit={e => {
                        e.preventDefault();
                        handleSubmit(query);
                    }}
                >
                    <input 
                        type="text" 
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Ask Copilot..."
                        className="flex-1 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2"
                        disabled={loading}
                    />
                    <button 
                        type="submit" 
                        disabled={loading || !query.trim()}
                        className="bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </form>
            </div>
        </div>
    );
};
