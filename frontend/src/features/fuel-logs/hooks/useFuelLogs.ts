import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fuelLogsApi } from "@/api/fuel-logs.api";
import type { CreateFuelLogPayload, UpdateFuelLogPayload } from "@/api/fuel-logs.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";

/**
 * Query keys for fuel log queries
 * Scoped under vehicle ID so invalidation is precise
 */
export const fuelLogKeys = {
    infinite: (vehicleId: string) => ["fuel-logs-infinite", vehicleId] as const,
};

function invalidateFuelDerivedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    vehicleId: string
) {
    queryClient.invalidateQueries({ queryKey: fuelLogKeys.infinite(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.details(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.analytics(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
}

/** Paginated fuel logs with Load more support for the vehicle detail Fuel tab */
export const useInfiniteFuelLogs = (vehicleId: string) => {
    return useInfiniteQuery({
        queryKey: fuelLogKeys.infinite(vehicleId),
        queryFn: ({ pageParam }) =>
            fuelLogsApi.getAll(vehicleId, {
                cursor: pageParam,
                size: 20,
            }),
        initialPageParam: undefined as string | undefined,
        getNextPageParam: (lastPage) =>
            lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
        enabled: !!vehicleId,
    });
};

/** Create a new fuel log */
export const useCreateFuelLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CreateFuelLogPayload) =>
            fuelLogsApi.create(vehicleId, payload),
        onSuccess: () => invalidateFuelDerivedQueries(queryClient, vehicleId),
    });
};

/** Update a fuel log */
export const useUpdateFuelLog = (vehicleId: string, logId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateFuelLogPayload) =>
            fuelLogsApi.update(vehicleId, logId, payload),
        onSuccess: () => invalidateFuelDerivedQueries(queryClient, vehicleId),
    });
};

/** Delete a fuel log */
export const useDeleteFuelLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (logId: string) => fuelLogsApi.delete(vehicleId, logId),
        onSuccess: () => invalidateFuelDerivedQueries(queryClient, vehicleId),
    });
};
