import apiClient from "@/lib/axios";
import type { CursorPage } from "@/types";
import {
    documentAllowsExpiry,
    type DocumentSchema,
    type DocumentTypeValue,
} from "@/features/documents/schemas";

/**
 * Document API calls.
 * All endpoints map to the backend /documents routes.
 * vehicle_id is passed as a query parameter.
 * File upload uses multipart/form-data (Content-Type left to the browser).
 */

export interface Document {
    id: string;
    vehicle_id: string;
    document_type: DocumentTypeValue;
    custom_label: string | null;
    identifier: string | null;
    display_label: string;
    expiry_date: string | null;
    notes: string | null;
    signed_url: string;
    days_until: number | null;
    expiry_status: "ok" | "soon" | "expired" | null;
}

export type UploadDocumentPayload = DocumentSchema & {
    file: File;
};

export type UpdateDocumentPayload = {
    document_type?: DocumentTypeValue;
    custom_label?: string | null;
    identifier?: string | null;
    expiry_date?: string | null;
    notes?: string | null;
    file?: File;
};

export const documentsApi = {
    getAll: async (
        vehicleId: string,
        params?: { cursor?: string; size?: number }
    ): Promise<CursorPage<Document>> => {
        const { data } = await apiClient.get("/documents/", {
            params: { vehicle_id: vehicleId, ...params },
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
        if (payload.document_type === "other" && payload.custom_label) {
            formData.append("custom_label", payload.custom_label.trim());
        }
        if (payload.identifier?.trim()) {
            formData.append("identifier", payload.identifier.trim());
        }
        if (documentAllowsExpiry(payload.document_type) && payload.expiry_date) {
            formData.append("expiry_date", payload.expiry_date);
        }
        if (payload.notes?.trim()) {
            formData.append("notes", payload.notes.trim());
        }

        const { data } = await apiClient.post("/documents/", formData, {
            params: { vehicle_id: vehicleId },
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
        if (payload.custom_label === null) {
            formData.append("clear_custom_label", "true");
        } else if (payload.custom_label !== undefined) {
            formData.append("custom_label", payload.custom_label);
        }
        if (payload.identifier === null) {
            formData.append("clear_identifier", "true");
        } else if (payload.identifier !== undefined) {
            formData.append("identifier", payload.identifier);
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
        });
        return data;
    },

    delete: async (vehicleId: string, documentId: string): Promise<void> => {
        await apiClient.delete(`/documents/${documentId}`, {
            params: { vehicle_id: vehicleId },
        });
    },
};
