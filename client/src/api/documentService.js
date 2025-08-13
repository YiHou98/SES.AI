import { apiClient } from './apiClient';

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Initiates the document upload in the background.
 * Sends the file and immediately returns a job ID for status tracking.
 * @param {File} file The file to upload.
 * @param {string} workspaceId The workspace/collection ID for the document.
 * @returns {Promise<{job_id: string}>} A promise that resolves to an object containing the job ID.
 */
export const backgroundUploadDocument = async (file, workspaceId) => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        throw new Error("No access token found. Please log in again.");
    }

    const formData = new FormData();
    formData.append('file', file);
    
    // Backend expects workspace_id, not collection_id
    if (workspaceId) {
        formData.append('workspace_id', workspaceId);
    } else {
        throw new Error("Workspace ID is required");
    }

    const response = await apiClient(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: {
            // For FormData, don't set Content-Type - let browser set it
            // apiClient will add Authorization header
        },
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'File upload failed');
    }
    return response.json(); // Returns { message, job_id }
};

/**
 * Polls the backend to get the status of a specific upload job.
 * @param {string} jobId The ID of the job to check.
 * @returns {Promise<{status: string, details: string}>} A promise that resolves to the job's status and details.
 */
export const getUploadStatus = async (jobId) => {
    const token = localStorage.getItem('accessToken');
    if (!token) throw new Error("No access token found.");

    const response = await apiClient(`${API_BASE_URL}/documents/upload/status/${jobId}`, {
        method: 'GET'
    });
    
    if (!response.ok) {
        throw new Error('Failed to fetch job status.');
    }
    return response.json(); // Returns { status, details }
};