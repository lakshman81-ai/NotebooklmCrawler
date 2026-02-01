const API_BASE = 'http://localhost:8000';

/**
 * Template Service - Handles Excel/CSV file operations via backend API
 */
export const templateService = {
    /**
     * Read template file from backend
     * @param {string} filepath - Relative path like "Harshitha/biology.xlsx"
     * @returns {Promise<Object>} File data with columns, rowCount, sampleData, etc.
     */
    async readTemplateFile(filepath) {
        try {
            const response = await fetch(`${API_BASE}/api/template/read`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Failed to read template: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Template read error:', error);
            throw error;
        }
    },

    /**
     * Upload user's Excel/CSV file
     * @param {File} file - File object from input
     * @returns {Promise<Object>} Parsed file data
     */
    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE}/api/template/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `Upload failed: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('File upload error:', error);
            throw error;
        }
    }
};
