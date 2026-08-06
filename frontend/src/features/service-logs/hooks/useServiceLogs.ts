import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { serviceLogsApi } from "@/api/service-logs.api";
import type {
    CreateServiceLogPayload,
    UpdateServiceLogPayload,
} from "@/api/service-logs.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";

/**
 * Query keys for service log queries
 * Scoped under vehicle ID so invalidation is precise
 */
export const serviceLogKeys = {
    all: (vehicleId: string) => ["service-logs", vehicleId] as const,
};

function invalidateServiceDerivedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    vehicleId: string
) {
    queryClient.invalidateQueries({ queryKey: serviceLogKeys.all(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.details(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
    queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
}

/** Fetch all service logs for a vehicle */
export const useServiceLogs = (vehicleId: string) => {
    return useQuery({
        queryKey: serviceLogKeys.all(vehicleId),
        queryFn: () => serviceLogsApi.getAll(vehicleId),
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
