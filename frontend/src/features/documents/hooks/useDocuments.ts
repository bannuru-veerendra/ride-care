import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
    infinite: (vehicleId: string) => ["documents-infinite", vehicleId] as const,
    details: (vehicleId: string, documentId: string) =>
        ["documents", vehicleId, documentId] as const,
};

function invalidateDocumentDerivedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    vehicleId: string
) {
    queryClient.invalidateQueries({ queryKey: documentKeys.infinite(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
}

/** Paginated documents with Load more support for the vehicle detail Docs tab */
export const useInfiniteDocuments = (vehicleId: string) => {
    return useInfiniteQuery({
        queryKey: documentKeys.infinite(vehicleId),
        queryFn: ({ pageParam }) =>
            documentsApi.getAll(vehicleId, {
                cursor: pageParam,
                size: 20,
            }),
        initialPageParam: undefined as string | undefined,
        getNextPageParam: (lastPage) =>
            lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
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
