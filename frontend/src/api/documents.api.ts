import apiClient from "@/lib/axios";

/**
 * Document API calls.
 * All endpoints map to the backend /documents routes.
 * vehicle_id is passed as a query parameter.
 * File upload uses multipart/form-data.
 */

export type DocumentType =
    | "insurance"
    | "driving_license"
    | "registration_certificate";

export interface Document {
    id: string;
    vehicle_id: string;
    document_type: DocumentType;
    original_filename: string;
    expiry_date: string | null;
    notes: string | null;
    signed_url: string;
    days_until: number | null;
    expiry_status: "ok" | "soon" | "expired" | null;
}

export interface UploadDocumentPayload {
    document_type: DocumentType;
    file: File;
    expiry_date?: string;
    notes?: string;
}

export interface UpdateDocumentPayload {
    document_type?: DocumentType;
    expiry_date?: string | null;
    notes?: string | null;
    file?: File;
}

export const documentsApi = {
    getAll: async (vehicleId: string): Promise<Document[]> => {
        const { data } = await apiClient.get("/documents/", {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    getById: async (vehicleId: string, documentId: string): Promise<Document> => {
        const { data } = await apiClient.get(`/documents/${documentId}`, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    upload: async (
        vehicleId: string,
        payload: UploadDocumentPayload
    ): Promise<Document> => {
        const formData = new FormData();
        formData.append("document_type", payload.document_type);
        formData.append("file", payload.file);
        if (payload.expiry_date) formData.append("expiry_date", payload.expiry_date);
        if (payload.notes) formData.append("notes", payload.notes);

        const { data } = await apiClient.post("/documents/", formData, {
            params: { vehicle_id: vehicleId },
            headers: { "Content-Type": "multipart/form-data" },
        });
        return data;
    },

    update: async (
        vehicleId: string,
        documentId: string,
        payload: UpdateDocumentPayload
    ): Promise<Document> => {
        const formData = new FormData();
        if (payload.document_type) {
            formData.append("document_type", payload.document_type);
        }
        if (payload.expiry_date === null) {
            formData.append("clear_expiry_date", "true");
        } else if (payload.expiry_date !== undefined) {
            formData.append("expiry_date", payload.expiry_date);
        }
        if (payload.notes === null) {
            formData.append("clear_notes", "true");
        } else if (payload.notes !== undefined) {
            formData.append("notes", payload.notes);
        }
        if (payload.file) formData.append("file", payload.file);

        const { data } = await apiClient.patch(`/documents/${documentId}`, formData, {
            params: { vehicle_id: vehicleId },
            headers: { "Content-Type": "multipart/form-data" },
        });
        return data;
    },

    delete: async (vehicleId: string, documentId: string): Promise<void> => {
        await apiClient.delete(`/documents/${documentId}`, {
            params: { vehicle_id: vehicleId },
        });
    },
};

export default documentsApi;
