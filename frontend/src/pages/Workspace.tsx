import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getInvestigation, updateInvestigation, createExperiment, runExperiment, getInvestigationMemory } from '../api/client';
import { ArrowLeft, Clock, Database, CheckCircle2, ChevronRight, Activity, Code2, FlaskConical, Target, Play, XCircle, BrainCircuit } from 'lucide-react';
import { CopilotPanel } from '../components/CopilotPanel';
import { Timeline } from '../components/Timeline';
import { formatDistanceToNow } from 'date-fns';

export const Workspace: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [inv, setInv] = useState<any>(null);
    const [error, setError] = useState<string>('');
    const [selectedFinding, setSelectedFinding] = useState<any>(null);
    const [selectedHypothesis, setSelectedHypothesis] = useState<any>(null);
    
    // Experiment drafting state
    const [draftSql, setDraftSql] = useState('');
    const [creatingExp, setCreatingExp] = useState(false);
    const [runningExp, setRunningExp] = useState<string | null>(null);

    // Resolution modal
    const [showResolveModal, setShowResolveModal] = useState(false);
    const [resolveRootCause, setResolveRootCause] = useState('');

    // Memory State
    const [memories, setMemories] = useState<any[]>([]);

    const loadData = async () => {
        try {
            const data = await getInvestigation(id!);
            setInv(data);
            if (!selectedFinding && data.findings?.length > 0) {
                setSelectedFinding(data.findings[0]);
            }
            
            const memoryData = await getInvestigationMemory(id!);
            setMemories(memoryData);
            
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message);
        }
    };

    useEffect(() => {
        loadData();
    }, [id]);

    const handleCreateExperiment = async (hypId: string) => {
        if (!draftSql.trim()) return;
        setCreatingExp(true);
        try {
            await createExperiment(inv.id, hypId, draftSql);
            setDraftSql('');
            await loadData();
        } catch (e) {
            console.error("Failed to create experiment", e);
        } finally {
            setCreatingExp(false);
        }
    };

    const handleRunExperiment = async (expId: string) => {
        setRunningExp(expId);
        try {
            await runExperiment(inv.id, expId);
            await loadData();
        } catch (e) {
            console.error("Failed to run experiment", e);
        } finally {
            setRunningExp(null);
        }
    };

    const handleResolve = async () => {
        if (!resolveRootCause.trim()) return;
        try {
            await updateInvestigation(inv.id, {
                status: 'RESOLVED',
                resolution: {
                    root_cause: resolveRootCause,
                    resolution_type: 'FIXED',
                    resolved_at: new Date().toISOString(),
                    validation_result: 'Verified'
                }
            });
            setShowResolveModal(false);
            await loadData();
        } catch (e) {
            console.error("Failed to resolve", e);
        }
    };

    if (error) return <div className="p-8 text-red-600">{error}</div>;
    if (!inv) return <div className="p-8 text-gray-500">Loading workspace...</div>;

    const getSeverityIcon = (severity: string) => {
        if (severity === 'CRITICAL' || severity === 'HIGH') return <div className="w-3 h-3 rounded-full bg-red-500" />;
        if (severity === 'MEDIUM') return <div className="w-3 h-3 rounded-full bg-yellow-500" />;
        return <div className="w-3 h-3 rounded-full bg-blue-500" />;
    };

    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden relative">
            {/* Left Panel */}
            <div className="w-[420px] min-w-[420px] border-r border-gray-200 bg-white flex flex-col h-full overflow-y-auto">
                <div className="p-5 border-b border-gray-200 bg-gray-50">
                    <Link to="/" className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1 mb-4">
                        <ArrowLeft className="w-4 h-4" /> Back to Inbox
                    </Link>
                    <div className="flex justify-between items-start mb-2">
                        <h1 className="text-xl font-bold text-gray-900">{inv.dataset_name} &middot; V{inv.dataset_version_number}</h1>
                        {inv.status !== 'RESOLVED' && (
                            <button 
                                onClick={() => setShowResolveModal(true)}
                                className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold uppercase rounded"
                            >
                                Resolve
                            </button>
                        )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                        <span className="flex items-center gap-1 bg-white border border-gray-200 px-2 py-1 rounded">
                            {inv.status === 'RESOLVED' ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <Activity className="w-4 h-4 text-blue-500" />}
                            {inv.status}
                        </span>
                        <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" /> {formatDistanceToNow(new Date(inv.created_at), { addSuffix: true })}
                        </span>
                    </div>
                </div>

                <div className="p-5 border-b border-gray-200">
                    <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 flex items-center justify-between">
                        Findings <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">{inv.findings?.length || 0}</span>
                    </h2>
                    <div className="space-y-3">
                        {inv.findings?.map((finding: any) => (
                            <div 
                                key={finding.id}
                                onClick={() => {
                                    setSelectedFinding(finding);
                                    setSelectedHypothesis(null);
                                }}
                                className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedFinding?.id === finding.id ? "border-blue-500 bg-blue-50/50" : "border-gray-200 hover:border-blue-300"}`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className="mt-1.5">{getSeverityIcon(finding.severity.value)}</div>
                                    <div>
                                        <div className="font-semibold text-gray-900 mb-1">{finding.title}</div>
                                        <div className="text-sm text-gray-600 line-clamp-2 mb-2">{finding.description}</div>
                                        <div className="text-xs text-gray-500 font-medium">
                                            {finding.evidence?.length || 0} Evidence &middot; {
                                                inv.hypotheses?.filter((h: any) => h.finding_id === finding.id).length
                                            } Hypotheses
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {memories.length > 0 && (
                    <div className="p-5 border-b border-gray-200 bg-blue-50/50">
                        <h2 className="text-sm font-bold text-blue-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <BrainCircuit className="w-4 h-4" /> Historical Precedent
                        </h2>
                        <div className="space-y-3">
                            {memories.map((mem) => (
                                <div key={mem.investigation_id} className="p-4 bg-white border border-blue-200 rounded-lg shadow-sm">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="font-semibold text-gray-900">{mem.title}</div>
                                        <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-0.5 rounded">{(mem.similarity_score * 100).toFixed(0)}% Match</span>
                                    </div>
                                    <div className="text-xs text-gray-500 mb-3 space-y-1">
                                        {mem.matched_factors.map((f: string, i: number) => <div key={i}>&bull; {f}</div>)}
                                    </div>
                                    <div className="bg-gray-50 border border-gray-200 p-3 rounded text-sm text-gray-700">
                                        <div className="font-semibold text-gray-900 mb-1">Resolved Root Cause</div>
                                        {mem.resolution_root_cause}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="p-5 flex-1">
                    <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Investigation Timeline</h2>
                    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                        <Timeline events={inv.timeline || []} />
                    </div>
                </div>
            </div>

            {/* Middle Panel */}
            <div className="flex-1 bg-gray-50 flex flex-col h-full overflow-y-auto relative">
                <div className="p-8 max-w-4xl w-full mx-auto pb-32">
                    {/* Resolution Banner */}
                    {inv.status === 'RESOLVED' && inv.resolution && (
                        <div className="mb-8 bg-green-50 border border-green-200 rounded-xl p-6">
                            <h2 className="text-lg font-bold text-green-900 flex items-center gap-2 mb-2">
                                <CheckCircle2 className="w-5 h-5" /> Investigation Resolved
                            </h2>
                            <div className="text-green-800">
                                <p className="mb-2"><strong>Root Cause:</strong> {inv.resolution.root_cause}</p>
                                <p className="text-sm">Resolved {formatDistanceToNow(new Date(inv.resolution.resolved_at), { addSuffix: true })}</p>
                            </div>
                        </div>
                    )}

                    {selectedFinding ? (
                        <div className="space-y-8">
                            <div>
                                <div className="flex items-center gap-2 text-sm font-medium text-blue-600 mb-2 uppercase tracking-wide">
                                    <Target className="w-4 h-4" /> Investigating Finding
                                </div>
                                <h2 className="text-3xl font-bold text-gray-900 mb-3">{selectedFinding.title}</h2>
                                <p className="text-lg text-gray-700 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                                    {selectedFinding.description}
                                </p>
                            </div>

                            <div>
                                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Database className="w-5 h-5 text-gray-500" /> Supporting Evidence
                                </h3>
                                <div className="bg-white border border-gray-200 rounded-xl shadow-sm divide-y divide-gray-100">
                                    {selectedFinding.evidence?.map((ev: any, idx: number) => (
                                        <div key={idx} className="p-4 flex flex-col gap-1">
                                            <div className="flex justify-between items-start">
                                                <span className="font-semibold text-gray-900">{ev.metric}</span>
                                                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded uppercase tracking-wide font-medium">{ev.source}</span>
                                            </div>
                                            <div className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded mt-2 border border-gray-200">
                                                {ev.value}
                                            </div>
                                            <div className="text-sm text-gray-500 mt-1">{ev.description}</div>
                                        </div>
                                    ))}
                                    {(!selectedFinding.evidence || selectedFinding.evidence.length === 0) && (
                                        <div className="p-6 text-center text-gray-500">No evidence collected.</div>
                                    )}
                                </div>
                            </div>

                            <div>
                                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <FlaskConical className="w-5 h-5 text-purple-500" /> Hypotheses & Experiments
                                </h3>
                                <div className="space-y-4">
                                    {inv.hypotheses?.filter((h: any) => h.finding_id === selectedFinding.id).map((hyp: any) => {
                                        const hypExps = inv.experiments?.filter((e: any) => e.hypothesis_id === hyp.id) || [];
                                        
                                        return (
                                        <div 
                                            key={hyp.id}
                                            onClick={() => setSelectedHypothesis(hyp.id === selectedHypothesis ? null : hyp.id)}
                                            className={`p-4 rounded-xl border transition-all ${hyp.id === selectedHypothesis ? 'border-blue-500 bg-blue-50/50' : 'border-gray-200 hover:border-blue-300'}`}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1 pr-6 cursor-pointer">
                                                    <div className="font-medium text-gray-900 mb-2">{hyp.description}</div>
                                                    <div className="flex items-center gap-3">
                                                        <span className={`text-xs px-2 py-1 rounded font-bold tracking-wide uppercase ${hyp.status === 'SUPPORTED' ? 'bg-green-100 text-green-700' : hyp.status === 'REJECTED' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                                                            {hyp.status}
                                                        </span>
                                                        <span className="text-xs text-gray-500 font-medium">
                                                            {hypExps.length} Experiment{hypExps.length !== 1 ? 's' : ''}
                                                        </span>
                                                    </div>
                                                </div>
                                                <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${hyp.id === selectedHypothesis ? 'rotate-90' : ''}`} />
                                            </div>

                                            {selectedHypothesis === hyp.id && (
                                                <div className="mt-6 pt-6 border-t border-purple-200" onClick={(e) => e.stopPropagation()}>
                                                    <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                                        <Code2 className="w-4 h-4 text-blue-500" /> Experiment Workspace
                                                    </h4>
                                                    
                                                    {hypExps.length === 0 ? (
                                                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                                                            <div className="text-sm font-medium text-gray-700 mb-2">Draft SQL Validation Query</div>
                                                            <textarea 
                                                                value={draftSql}
                                                                onChange={(e) => setDraftSql(e.target.value)}
                                                                placeholder="SELECT * FROM dataset WHERE..."
                                                                className="w-full bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm shadow-inner mb-4 min-h-[120px] outline-none focus:ring-2 focus:ring-blue-500"
                                                            />
                                                            <div className="flex justify-end gap-3">
                                                                <button 
                                                                    onClick={() => handleCreateExperiment(hyp.id)}
                                                                    disabled={creatingExp || !draftSql.trim()}
                                                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                                                >
                                                                    {creatingExp ? 'Saving...' : 'Draft Experiment'}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="space-y-4">
                                                            {hypExps.map((exp: any) => (
                                                                <div key={exp.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                                                                    <div className="bg-gray-900 text-gray-100 p-4 font-mono text-sm shadow-inner overflow-x-auto whitespace-pre">
                                                                        {exp.sql_query}
                                                                    </div>
                                                                    <div className="p-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                                                                        <div className="flex items-center gap-3">
                                                                            <span className={`text-xs px-2 py-1 rounded font-bold uppercase ${exp.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                                                                                {exp.status}
                                                                            </span>
                                                                            <span className="text-xs text-gray-500">
                                                                                Drafted by {exp.requested_by}
                                                                            </span>
                                                                        </div>
                                                                        
                                                                        {exp.status !== 'COMPLETED' && exp.status !== 'FAILED' && (
                                                                            <button 
                                                                                onClick={() => handleRunExperiment(exp.id)}
                                                                                disabled={runningExp === exp.id}
                                                                                className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                                                                            >
                                                                                {runningExp === exp.id ? <Activity className="w-4 h-4 animate-pulse" /> : <Play className="w-4 h-4 fill-current" />}
                                                                                {runningExp === exp.id ? 'Running...' : 'Run Analysis'}
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                    
                                                                    {exp.result && (
                                                                        <div className="p-4 border-t border-gray-200 bg-white">
                                                                            <h5 className="text-xs font-bold text-gray-500 uppercase mb-3">Execution Result</h5>
                                                                            
                                                                            {exp.result.error_message ? (
                                                                                <div className="bg-red-50 text-red-700 p-3 rounded-lg border border-red-100 flex items-start gap-2 font-mono text-sm">
                                                                                    <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                                                                    {exp.result.error_message}
                                                                                </div>
                                                                            ) : (
                                                                                <div>
                                                                                    <div className="flex gap-4 mb-3 text-sm text-gray-600 font-medium">
                                                                                        <span className="bg-gray-100 px-2 py-1 rounded">{exp.result.row_count} Rows matched</span>
                                                                                        <span className="bg-gray-100 px-2 py-1 rounded">{exp.result.execution_time_ms.toFixed(1)}ms execution</span>
                                                                                    </div>
                                                                                    
                                                                                    {exp.result.sample_rows?.length > 0 && (
                                                                                        <div className="overflow-x-auto border border-gray-200 rounded-lg">
                                                                                            <table className="min-w-full divide-y divide-gray-200 text-sm">
                                                                                                <thead className="bg-gray-50">
                                                                                                    <tr>
                                                                                                        {exp.result.columns.map((col: string) => (
                                                                                                            <th key={col} className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">{col}</th>
                                                                                                        ))}
                                                                                                    </tr>
                                                                                                </thead>
                                                                                                <tbody className="bg-white divide-y divide-gray-200">
                                                                                                    {exp.result.sample_rows.map((row: any, i: number) => (
                                                                                                        <tr key={i}>
                                                                                                            {exp.result.columns.map((col: string) => (
                                                                                                                <td key={col} className="px-4 py-2 whitespace-nowrap text-gray-900 font-mono text-xs">{String(row[col])}</td>
                                                                                                            ))}
                                                                                                        </tr>
                                                                                                    ))}
                                                                                                </tbody>
                                                                                            </table>
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )})}
                                    {inv.hypotheses?.filter((h: any) => h.finding_id === selectedFinding.id).length === 0 && (
                                        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500 shadow-sm">
                                            No hypotheses generated yet. Use Copilot to propose some.
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 pt-20">
                            <Target className="w-12 h-12 text-gray-300 mb-4" />
                            <h2 className="text-xl font-medium text-gray-900 mb-2">Select a finding to investigate</h2>
                            <p>Choose a finding from the left panel to view evidence and test hypotheses.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel: Copilot */}
            <div className="w-[400px] min-w-[400px] border-l border-gray-200 bg-white flex flex-col h-full shadow-lg z-10">
                <CopilotPanel investigationId={inv.id} context={{ selectedFinding, selectedHypothesis, memories }} />
            </div>

            {/* Resolve Modal */}
            {showResolveModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                    <div className="bg-white rounded-xl shadow-2xl p-6 max-w-lg w-full">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Resolve Investigation</h2>
                        <p className="text-sm text-gray-600 mb-4">Record the verified root cause to close this investigation and train DataForge for future memory.</p>
                        <textarea
                            value={resolveRootCause}
                            onChange={(e) => setResolveRootCause(e.target.value)}
                            placeholder="e.g., An upstream batch job dropped the email column, leading to a 100% null rate."
                            className="w-full border border-gray-300 rounded-lg p-3 h-32 mb-4 text-sm"
                        />
                        <div className="flex justify-end gap-3">
                            <button 
                                onClick={() => setShowResolveModal(false)}
                                className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium text-sm"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleResolve}
                                disabled={!resolveRootCause.trim()}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium text-sm rounded-lg disabled:opacity-50"
                            >
                                Resolve Investigation
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

