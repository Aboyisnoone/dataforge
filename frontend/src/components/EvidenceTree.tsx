import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Database, Info, Play, CheckCircle2, XCircle, Clock, Plus } from 'lucide-react';
import type { Finding, Hypothesis, Experiment } from '../types/api';
import { api } from '../api/client';

const TreeNode: React.FC<{
    title: React.ReactNode;
    icon: React.ReactNode;
    isLast: boolean;
    children?: React.ReactNode;
    defaultExpanded?: boolean;
    badge?: React.ReactNode;
}> = ({ title, icon, isLast, children, defaultExpanded = false, badge }) => {
    const [expanded, setExpanded] = useState(defaultExpanded);
    const hasChildren = !!children;

    return (
        <div className="relative flex">
            {!isLast && (
                <div className="absolute top-6 left-[11px] w-px h-[calc(100%-24px)] bg-gray-200" />
            )}
            <div className="flex flex-col w-full">
                <div 
                    className={`flex items-center py-2 ${hasChildren ? 'cursor-pointer hover:bg-gray-50' : ''} rounded`}
                    onClick={() => hasChildren && setExpanded(!expanded)}
                >
                    <div className="w-6 flex items-center justify-center text-gray-400">
                        {hasChildren ? (expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />) : <div className="w-4" />}
                    </div>
                    <div className="text-gray-500 mr-2">
                        {icon}
                    </div>
                    <div className="font-medium text-gray-900 text-sm flex-1 flex items-center gap-2">
                        {title}
                        {badge}
                    </div>
                </div>
                {expanded && hasChildren && (
                    <div className="ml-8 mt-1 mb-2 text-sm text-gray-700">
                        {children}
                    </div>
                )}
            </div>
        </div>
    );
};

export const EvidenceGraph: React.FC<{ 
    investigationId: string;
    finding: Finding; 
    hypotheses: Hypothesis[]; 
    experiments?: Experiment[]; 
    onExperimentsChanged?: () => void;
}> = ({ investigationId, finding, hypotheses, experiments = [], onExperimentsChanged }) => {
    
    const [draftingFor, setDraftingFor] = useState<string | null>(null);
    const [draftQuery, setDraftQuery] = useState('');
    const [runningExps, setRunningExps] = useState<Set<string>>(new Set());
    
    const evidence = finding.evidence || [];
    
    const getRelevanceColor = (relevance: string) => {
        if (relevance === 'HIGH') return 'bg-green-100 text-green-700 border-green-200';
        if (relevance === 'MEDIUM') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
        if (relevance === 'LOW') return 'bg-gray-100 text-gray-700 border-gray-200';
        return 'bg-gray-100 text-gray-700 border-gray-200';
    };

    const getRelevanceLabel = (relevance: string) => {
        if (relevance === 'HIGH') return 'STRONG';
        if (relevance === 'MEDIUM') return 'PLAUSIBLE';
        if (relevance === 'LOW') return 'UNLIKELY';
        return 'UNKNOWN';
    };
    
    const handleSaveDraft = async (hypId: string) => {
        if (!draftQuery.trim()) return;
        try {
            await api.post(`/investigations/${investigationId}/hypotheses/${hypId}/experiments`, {
                sql_query: draftQuery,
                requested_by: 'Engineer'
            });
            setDraftingFor(null);
            setDraftQuery('');
            if (onExperimentsChanged) onExperimentsChanged();
        } catch (err) {
            console.error('Failed to save draft:', err);
        }
    };
    
    const handleRunExperiment = async (expId: string) => {
        setRunningExps(prev => new Set(prev).add(expId));
        try {
            await api.post(`/investigations/${investigationId}/experiments/${expId}/run`);
            if (onExperimentsChanged) onExperimentsChanged();
        } catch (err) {
            console.error('Failed to run exp:', err);
        } finally {
            setRunningExps(prev => {
                const next = new Set(prev);
                next.delete(expId);
                return next;
            });
        }
    };

    return (
        <div className="bg-white border-t border-gray-100 p-4 rounded-b-lg">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Evidence Graph</h4>
            
            <div className="pl-2">
                {evidence.map((ev, idx) => {
                    const isLast = (idx === evidence.length - 1) && hypotheses.length === 0;
                    return (
                        <TreeNode
                            key={ev.id}
                            title={<span>Evidence: {ev.description || ev.metric}</span>}
                            icon={<Database className="w-4 h-4 text-blue-500" />}
                            isLast={isLast}
                        >
                            <div className="bg-gray-50 border border-gray-100 rounded p-3 mt-1 inline-block min-w-[250px]">
                                <div className="text-xs text-gray-500 mb-1 uppercase">Source: {ev.source}</div>
                                <div className="font-mono text-xs">{String(ev.value)}</div>
                            </div>
                        </TreeNode>
                    );
                })}
                
                {hypotheses.map((hyp, idx) => {
                    const isLast = idx === hypotheses.length - 1;
                    const attrEv = evidence.find(e => e.metric === 'attribution_match' && hyp.description.includes(e.description.replace('Attribution match: ', '')));
                    const relevanceRaw = attrEv ? String(attrEv.value) : 'LOW';
                    
                    const hypExperiments = experiments.filter(e => e.hypothesis_id === hyp.id);

                    return (
                        <TreeNode
                            key={hyp.id}
                            title={<span>Hypothesis: {hyp.description}</span>}
                            icon={<Info className="w-4 h-4 text-indigo-500" />}
                            isLast={isLast}
                            defaultExpanded={relevanceRaw === 'HIGH'}
                            badge={
                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${getRelevanceColor(relevanceRaw)}`}>
                                    {getRelevanceLabel(relevanceRaw)}
                                </span>
                            }
                        >
                            <div className="pl-4 border-l-2 border-indigo-100 py-1 space-y-3">
                                <div className="text-xs text-gray-600">
                                    <span className="font-semibold">Status:</span> {hyp.status}
                                </div>
                                
                                {hypExperiments.length > 0 && (
                                    <div className="space-y-2 mt-2">
                                        <div className="text-[10px] font-bold text-gray-400 uppercase">Experiments</div>
                                        {hypExperiments.map(exp => (
                                            <div key={exp.id} className="bg-white border border-gray-200 rounded p-3 text-sm shadow-sm">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="font-medium text-gray-900 flex items-center gap-2">
                                                        <Database className="w-3.5 h-3.5 text-gray-500" />
                                                        SQL Query
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                                            {exp.status}
                                                        </span>
                                                        {exp.status === 'DRAFT' && (
                                                            <button 
                                                                onClick={() => handleRunExperiment(exp.id)}
                                                                disabled={runningExps.has(exp.id)}
                                                                className="flex items-center gap-1 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-2 py-1 rounded text-xs font-medium transition-colors disabled:opacity-50"
                                                            >
                                                                {runningExps.has(exp.id) ? <Clock className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                                                                Run
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                                <pre className="bg-gray-900 text-gray-100 p-2 rounded text-xs overflow-x-auto mb-2">
                                                    {exp.sql_query}
                                                </pre>
                                                
                                                {exp.result && (
                                                    <div className="mt-3 pt-3 border-t border-gray-100">
                                                        <div className="flex items-center gap-4 text-xs mb-2">
                                                            {exp.status === 'COMPLETED' ? (
                                                                <div className="flex items-center gap-1 text-emerald-600">
                                                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                                                    Success ({exp.result.row_count} rows)
                                                                </div>
                                                            ) : (
                                                                <div className="flex items-center gap-1 text-red-600">
                                                                    <XCircle className="w-3.5 h-3.5" />
                                                                    Failed
                                                                </div>
                                                            )}
                                                            <div className="flex items-center gap-1 text-gray-500">
                                                                <Clock className="w-3.5 h-3.5" />
                                                                {exp.result.execution_time_ms.toFixed(0)}ms
                                                            </div>
                                                        </div>
                                                        {exp.result.error_message && (
                                                            <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                                                                {exp.result.error_message}
                                                            </div>
                                                        )}
                                                        {exp.result.sample_rows && exp.result.sample_rows.length > 0 && (
                                                            <div className="mt-2 text-[10px] font-mono bg-gray-50 p-2 rounded border border-gray-200">
                                                                <div className="text-gray-400 font-bold mb-1 border-b border-gray-200 pb-1">
                                                                    Sample Results
                                                                </div>
                                                                {exp.result.sample_rows.slice(0, 3).map((r, i) => (
                                                                    <div key={i} className="truncate">{JSON.stringify(r)}</div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                                
                                {draftingFor !== hyp.id ? (
                                    <button 
                                        onClick={() => setDraftingFor(hyp.id)}
                                        className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 mt-2"
                                    >
                                        <Plus className="w-3 h-3" /> Draft SQL Experiment
                                    </button>
                                ) : (
                                    <div className="bg-gray-50 border border-gray-200 p-3 rounded mt-2">
                                        <div className="text-xs text-gray-500 mb-2 font-medium">Draft SQL Query</div>
                                        <textarea
                                            className="w-full text-xs font-mono p-2 border border-gray-300 rounded focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                                            rows={4}
                                            value={draftQuery}
                                            onChange={e => setDraftQuery(e.target.value)}
                                            placeholder="SELECT * FROM dataset LIMIT 10"
                                        />
                                        <div className="flex justify-end gap-2 mt-2">
                                            <button 
                                                onClick={() => setDraftingFor(null)}
                                                className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1"
                                            >
                                                Cancel
                                            </button>
                                            <button 
                                                onClick={() => handleSaveDraft(hyp.id)}
                                                className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded"
                                            >
                                                Save Draft
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </TreeNode>
                    );
                })}
            </div>
        </div>
    );
};
