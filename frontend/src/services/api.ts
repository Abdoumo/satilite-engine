const isProd = import.meta.env.PROD;
export const API_BASE_URL = isProd 
    ? `${window.location.protocol}//${window.location.hostname}:8899/api`
    : 'http://localhost:8000/api';

export async function fetchPipelines() {
    const res = await fetch(`${API_BASE_URL}/pipelines`);
    return res.json();
}

export async function fetchPipelineSegments(pipelineId: number) {
    const res = await fetch(`${API_BASE_URL}/pipelines/${pipelineId}/segments`);
    return res.json();
}

export async function fetchCameras() {
    const res = await fetch(`${API_BASE_URL}/cameras`);
    return res.json();
}

export async function fetchDrones() {
    const res = await fetch(`${API_BASE_URL}/drones`);
    return res.json();
}

export async function fetchAlerts() {
    const res = await fetch(`${API_BASE_URL}/alerts`);
    return res.json();
}
