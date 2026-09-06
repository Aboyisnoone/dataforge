import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getInvestigations } from '../api/client';
import { Search, AlertCircle, Clock, CheckCircle2, CircleDashed } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const Inbox: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [error, setError] = useState<string>('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchInvestigations = async () => {
            const params: any = {};
            if (statusFilter) params.status = statusFilter;
            if (searchQuery) params.search = searchQuery;
            
            try {
                const res = await getInvestigations(params);
                setData(res);
                setError('');
            } catch (error: any) {
                console.error("Failed to fetch investigations", error);
                setError("Failed to load investigations. Please ensure the API is running.");
            }
        };
        
        // Debounce search
        const timeoutId = setTimeout(fetchInvestigations, 300);
        return () => clearTimeout(timeoutId);
    }, [statusFilter, searchQuery]);

    const getSeverityIcon = (inv: any) => {
        if (inv.status === 'RESOLVED') return <CheckCircle2 className="w-5 h-5 text-green-500 mt-1" />;
        
        if (inv.highest_severity === 'CRITICAL' || inv.highest_severity === 'HIGH') {
            return <div className="w-3 h-3 rounded-full bg-red-500 mt-2" />;
        }
        if (inv.highest_severity === 'MEDIUM') {
            return <div className="w-3 h-3 rounded-full bg-yellow-500 mt-2" />;
        }
        return <div className="w-3 h-3 rounded-full bg-blue-500 mt-2" />;
    };

    const tabs = [
        { id: '', label: 'All' },
        { id: 'OPEN', label: 'Open' },
        { id: 'INVESTIGATING', label: 'Investigating' },
        { id: 'RESOLVED', label: 'Resolved' }
    ];

    return (
        <div className="max-w-5xl mx-auto p-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Investigations</h1>
                <div className="relative">
                    <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                    <input 
                        type="text" 
                        placeholder="Search..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-64 transition-all"
                    />
                </div>
            </div>

            <div className="flex gap-4 mb-6 border-b border-gray-200">
                {tabs.map(tab => (
                    <button
                        key={tab.label}
                        onClick={() => setStatusFilter(tab.id)}
                        className={pb-3 px-1 font-medium text-sm transition-colors border-b-2 \}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-6 flex items-center gap-3">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            <div className="space-y-4">
                {data?.items?.map((inv: any) => (
                    <div 
                        key={inv.id} 
                        onClick={() => navigate(/investigations/\)}
                        className="bg-white p-5 rounded-xl border border-gray-200 hover:shadow-md hover:border-gray-300 cursor-pointer transition-all flex gap-4"
                    >
                        <div className="flex-shrink-0 flex justify-center">
                            {getSeverityIcon(inv)}
                        </div>
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                {inv.findings?.[0]?.title || inv.title}
                            </h3>
                            <div className="text-sm font-medium text-gray-500 mb-2">
                                {inv.dataset_name} &middot; V{inv.dataset_version_number}
                            </div>
                            
                            {inv.status === 'RESOLVED' ? (
                                <div className="text-gray-600 mb-3">
                                    Resolved
                                </div>
                            ) : (
                                <div className="text-gray-700 mb-3 line-clamp-2">
                                    {inv.findings?.[0]?.description || inv.description}
                                </div>
                            )}

                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                {inv.status !== 'RESOLVED' && (
                                    <div className="flex items-center gap-1 font-medium text-gray-600">
                                        <CircleDashed className="w-4 h-4" />
                                        {inv.hypotheses?.length || 0} hypotheses &middot; {
                                            inv.strong_candidates_count === 0 ? 'No validated cause' : 
                                            \ strong candidate\
                                        }
                                    </div>
                                )}
                                <div className="flex items-center gap-1">
                                    <Clock className="w-4 h-4" />
                                    {formatDistanceToNow(new Date(inv.created_at), { addSuffix: true })}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
                
                {data?.items?.length === 0 && !error && (
                    <div className="text-center py-12 text-gray-500 bg-white border border-gray-200 rounded-xl border-dashed">
                        No investigations found.
                    </div>
                )}
            </div>
        </div>
    );
};
