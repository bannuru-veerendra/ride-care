import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { serviceLogsApi } from "@/api/service-logs.api";
import type {
    CreateServiceLogPayload,
    UpdateServiceLogPayload,
} from "@/api/service-logs.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";
import { getCursorNextPageParam } from "@/lib/query-client";

/**
 * Query keys for service log queries
 * Scoped under vehicle ID so invalidation is precise
 */
export const serviceLogKeys = {
    infinite: (vehicleId: string) => ["service-logs-infinite", vehicleId] as const,
};

function invalidateServiceDerivedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    vehicleId: string
) {
    queryClient.invalidateQueries({ queryKey: serviceLogKeys.infinite(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.details(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
}

/** Paginated service logs with Load more support */
export const useInfiniteServiceLogs = (vehicleId: string) => {
    return useInfiniteQuery({
        queryKey: serviceLogKeys.infinite(vehicleId),
        queryFn: ({ pageParam }) =>
            serviceLogsApi.getAll(vehicleId, {
                cursor: pageParam,
                size: 20,
            }),
        initialPageParam: undefined as string | undefined,
        getNextPageParam: getCursorNextPageParam,
        enabled: !!vehicleId,
    });
};

/** Create a new service log */
export const useCreateServiceLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CreateServiceLogPayload) =>
            serviceLogsApi.create(vehicleId, payload),
        onSuccess: () => invalidateServiceDerivedQueries(queryClient, vehicleId),
    });
};

/** Update a service log */
export const useUpdateServiceLog = (vehicleId: string, logId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateServiceLogPayload) =>
            serviceLogsApi.update(vehicleId, logId, payload),
        onSuccess: () => invalidateServiceDerivedQueries(queryClient, vehicleId),
    });
};

/** Delete a service log */
export const useDeleteServiceLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (logId: string) => serviceLogsApi.delete(vehicleId, logId),
        onSuccess: () => invalidateServiceDerivedQueries(queryClient, vehicleId),
    });
};
