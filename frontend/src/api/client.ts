import axios from 'axios';
import type { PaginatedInvestigations, Investigation, InvestigationStatus, Resolution } from '../types/api';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: apiUrl
});

export const getInvestigations = async (params?: {
    status?: string;
    severity?: string;
    search?: string;
    skip?: number;
    limit?: number;
}): Promise<PaginatedInvestigations> => {
    const response = await api.get('/investigations', { params });
    return response.data;
};

export const getInvestigation = async (id: string): Promise<Investigation> => {
    const response = await api.get(`/investigations/${id}`);
    return response.data;
};

export const getInvestigationMemory = async (id: string): Promise<Resolution[]> => {
    const response = await api.get(`/investigations/${id}/memory`);
    return response.data;
};

export const resolveInvestigation = async (id: string, resolution: any): Promise<any> => {
    const response = await api.post(`/investigations/${id}/resolve`, resolution);
    return response.data;
};

export const addHypothesis = async (id: string, hypothesis: any): Promise<any> => {
    const response = await api.post(`/investigations/${id}/hypotheses`, hypothesis);
    return response.data;
};

export const updateHypothesisStatus = async (id: string, hypothesisId: string, status: string): Promise<any> => {
    const response = await api.patch(`/investigations/${id}/hypotheses/${hypothesisId}/status`, { status });
    return response.data;
};

export const executeExperiment = async (id: string, experiment: any): Promise<any> => {
    const response = await api.post(`/investigations/${id}/experiments`, experiment);
    return response.data;
};

export const askCopilot = async (id: string, query: string, context?: any): Promise<any> => {
    const response = await api.post(`/investigations/${id}/copilot`, { query, context });
    return response.data;
};

export const uploadDataset = async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/datasets', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getDatasets = async (): Promise<any> => {
    const response = await api.get('/datasets');
    return response.data;
};
