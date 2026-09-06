import axios from 'axios';
import type { PaginatedInvestigations, Investigation, InvestigationStatus, Resolution } from '../types/api';

export const api = axios.create({
    baseURL: 'http://localhost:8000'
});

export const getInvestigations = async (params?: {
    status?: string;
    severity?: string;
    dataset_id?: string;
    search?: string;
    page?: number;
    page_size?: number;
}): Promise<PaginatedInvestigations> => {
    const response = await api.get('/investigations', { params });
    return response.data;
};

export const getInvestigation = async (id: string): Promise<Investigation> => {
    const response = await api.get(\/investigations/\\);
    return response.data;
};

export const getInvestigationMemory = async (id: string): Promise<any[]> => {
    const response = await api.get(\/investigations/\/memory\);
    return response.data;
};

export const updateInvestigation = async (id: string, update: {
    status: InvestigationStatus;
    resolution?: Resolution;
}): Promise<Investigation> => {
    const response = await api.patch(\/investigations/\\, update);
    return response.data;
};

export const askCopilot = async (id: string, query: string, context?: any): Promise<any> => {
    const response = await api.post(\/investigations/\/copilot\, { query, context });
    return response.data;
};

export const createExperiment = async (invId: string, hypothesisId: string, sqlQuery: string): Promise<any> => {
    const response = await api.post(\/investigations/\/hypotheses/\/experiments\, {
        sql_query: sqlQuery,
        requested_by: "Engineer"
    });
    return response.data;
};

export const runExperiment = async (invId: string, experimentId: string): Promise<any> => {
    const response = await api.post(\/investigations/\/experiments/\/run\);
    return response.data;
};
