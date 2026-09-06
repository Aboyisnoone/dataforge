import React from 'react';
import type { TimelineEvent } from '../types/api';
import { Activity, Database, FileDiff, Target, AlertTriangle, ShieldCheck, CheckCircle, Info } from 'lucide-react';

export const Timeline: React.FC<{ events: TimelineEvent[] }> = ({ events }) => {
    
    const getIcon = (type: string) => {
        switch(type) {
            case 'DATASET_VERSION_CREATED': return <Database className="w-4 h-4" />;
            case 'HISTORICAL_CHANGE_DISCOVERED': return <FileDiff className="w-4 h-4" />;
            case 'FINDING_DETECTED': return <AlertTriangle className="w-4 h-4" />;
            case 'EVIDENCE_COLLECTED': return <Target className="w-4 h-4" />;
            case 'ATTRIBUTION_GENERATED': return <ShieldCheck className="w-4 h-4" />;
            case 'STATUS_CHANGED': return <Activity className="w-4 h-4" />;
            case 'HYPOTHESIS_CREATED': return <Info className="w-4 h-4" />;
            case 'RESOLUTION_CREATED': return <CheckCircle className="w-4 h-4" />;
            default: return <Activity className="w-4 h-4" />;
        }
    };

    const getColor = (type: string) => {
        switch(type) {
            case 'DATASET_VERSION_CREATED': return 'bg-blue-100 text-blue-600 ring-blue-50';
            case 'HISTORICAL_CHANGE_DISCOVERED': return 'bg-purple-100 text-purple-600 ring-purple-50';
            case 'FINDING_DETECTED': return 'bg-red-100 text-red-600 ring-red-50';
            case 'EVIDENCE_COLLECTED': return 'bg-orange-100 text-orange-600 ring-orange-50';
            case 'ATTRIBUTION_GENERATED': return 'bg-green-100 text-green-600 ring-green-50';
            case 'HYPOTHESIS_CREATED': return 'bg-indigo-100 text-indigo-600 ring-indigo-50';
            case 'STATUS_CHANGED': return 'bg-gray-100 text-gray-600 ring-gray-50';
            case 'RESOLUTION_CREATED': return 'bg-emerald-100 text-emerald-600 ring-emerald-50';
            default: return 'bg-gray-100 text-gray-600 ring-gray-50';
        }
    };

    if (!events || events.length === 0) {
        return <div className="text-gray-500 text-sm p-8 text-center border rounded-lg bg-gray-50">No timeline events recorded.</div>;
    }

    return (
        <div className="flow-root bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" /> Investigation Timeline
            </h2>
            <ul role="list" className="-mb-8">
                {events.map((event, eventIdx) => (
                    <li key={event.id}>
                        <div className="relative pb-8">
                            {eventIdx !== events.length - 1 ? (
                                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                            ) : null}
                            <div className="relative flex space-x-3">
                                <div>
                                    <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ${getColor(event.event_type)}`}>
                                        {getIcon(event.event_type)}
                                    </span>
                                </div>
                                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                                    <div>
                                        <p className="text-sm text-gray-900 font-bold">{event.event_type.replace(/_/g, ' ')}</p>
                                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                                        {event.metadata && Object.keys(event.metadata).length > 0 && (
                                            <div className="mt-2 text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded border border-gray-100 inline-block shadow-sm">
                                                {Object.entries(event.metadata).map(([k, v]) => (
                                                    <div key={k}><span className="text-gray-400 font-bold">{k}:</span> {String(v)}</div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <div className="whitespace-nowrap text-right text-xs font-medium text-gray-500">
                                        {new Date(event.timestamp).toLocaleString(undefined, {
                                            month: 'short', day: 'numeric', year: 'numeric',
                                            hour: 'numeric', minute: '2-digit'
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};
