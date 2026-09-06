import React, { useState, useRef, useEffect } from 'react';
import { Upload, Database, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';

export const Datasets = () => {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const fileInput = useRef<HTMLInputElement>(null);
    
    const loadDatasets = async () => {
        try {
            const res = await api.get('/datasets');
            setDatasets(res.data || []);
        } catch (err) {
            console.error("Failed to load datasets", err);
        }
    };

    useEffect(() => {
        loadDatasets();
    }, []);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const ext = file.name.split('.').pop()?.toLowerCase();
            if (!['csv', 'parquet', 'json', 'ndjson'].includes(ext || '')) {
                throw new Error("Unsupported format. Use CSV, Parquet, JSON, or NDJSON.");
            }

            const res = await api.post('/datasets', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            setSuccess(`Successfully uploaded version ${res.data.version_number} of dataset ${res.data.dataset_id}`);
            loadDatasets();
        } catch (err: any) {
            console.error(err);
            if (err.response?.status === 413) {
                setError("File is too large (Maximum 1GB).");
            } else {
                setError(err.response?.data?.detail || err.message || "Upload failed");
            }
        } finally {
            setUploading(false);
            if (fileInput.current) fileInput.current.value = '';
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Datasets</h1>
            
            <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm mb-8 text-center">
                <Upload className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                <h2 className="text-lg font-semibold mb-2">Upload a Dataset</h2>
                <p className="text-gray-500 mb-6">Upload a CSV, Parquet, JSON, or NDJSON file to analyze. If the filename matches an existing dataset, it will be added as a new version automatically.</p>
                
                <input 
                    type="file" 
                    ref={fileInput} 
                    className="hidden" 
                    onChange={handleUpload}
                    accept=".csv,.parquet,.json,.ndjson"
                />
                
                <button 
                    onClick={() => fileInput.current?.click()}
                    disabled={uploading}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                    {uploading ? 'Uploading & Analyzing...' : 'Select File'}
                </button>

                {error && (
                    <div className="mt-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center gap-2 max-w-md mx-auto text-left">
                        <AlertCircle className="w-5 h-5 flex-shrink-0" /> {error}
                    </div>
                )}
                {success && (
                    <div className="mt-4 p-3 bg-green-50 text-green-700 border border-green-200 rounded-lg flex items-center gap-2 max-w-md mx-auto text-left">
                        <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> {success}
                    </div>
                )}
            </div>
            
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-700">Dataset History</h3>
                </div>
                {datasets.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        <Database className="w-8 h-8 mx-auto mb-3 text-gray-400" />
                        <p>No datasets found.</p>
                        <p className="text-sm">Upload a dataset above to get started.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-gray-200">
                        {datasets.map(d => (
                            <div key={d.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                                <div>
                                    <h4 className="font-medium text-gray-900">{d.name}</h4>
                                    <p className="text-sm text-gray-500">
                                        Latest: v{d.latest_version.version_number} &bull; {d.latest_version.row_count.toLocaleString()} rows &bull; {d.latest_version.format.toUpperCase()}
                                    </p>
                                </div>
                                <div className="text-sm text-gray-500">
                                    {new Date(d.latest_version.created_at).toLocaleDateString()}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

