import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/api/documents.api";
import type {
    UploadDocumentPayload,
    UpdateDocumentPayload,
} from "@/api/documents.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";

/**
 * Query keys for document queries.
 * Scoped under vehicle ID so invalidation is precise.
 */
export const documentKeys = {
    all: (vehicleId: string) => ["documents", vehicleId] as const,
    details: (vehicleId: string, documentId: string) =>
        ["documents", vehicleId, documentId] as const,
};

function invalidateDocumentDerivedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    vehicleId: string
) {
    queryClient.invalidateQueries({ queryKey: documentKeys.all(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
}

/** Fetch all documents for a vehicle */
export const useDocuments = (vehicleId: string) => {
    return useQuery({
        queryKey: documentKeys.all(vehicleId),
        queryFn: () => documentsApi.getAll(vehicleId),
        enabled: !!vehicleId,
    });
};

/** Upload a new document */
export const useUploadDocument = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UploadDocumentPayload) =>
            documentsApi.upload(vehicleId, payload),
        onSuccess: () => invalidateDocumentDerivedQueries(queryClient, vehicleId),
    });
};

/** Update a document */
export const useUpdateDocument = (vehicleId: string, documentId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateDocumentPayload) =>
            documentsApi.update(vehicleId, documentId, payload),
        onSuccess: () => invalidateDocumentDerivedQueries(queryClient, vehicleId),
    });
};

/** Delete a document */
export const useDeleteDocument = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (documentId: string) =>
            documentsApi.delete(vehicleId, documentId),
        onSuccess: () => invalidateDocumentDerivedQueries(queryClient, vehicleId),
    });
};
