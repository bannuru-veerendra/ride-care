import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { serviceLogsApi } from "@/api/service-logs.api";
import type {
    CreateServiceLogPayload,
    UpdateServiceLogPayload,
} from "@/api/service-logs.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";

/**
 * Query keys for service log queries.
 * Scoped under vehicle ID so invalidation is precise.
 */
export const serviceLogKeys = {
    all: (vehicleId: string) => ["service-logs", vehicleId] as const,
    next: (vehicleId: string) => ["service-logs", vehicleId, "next"] as const,
    details: (vehicleId: string, logId: string) =>
        ["service-logs", vehicleId, logId] as const,
};

/** Fetch all service logs for a vehicle */
export const useServiceLogs = (vehicleId: string) => {
    return useQuery({
        queryKey: serviceLogKeys.all(vehicleId),
        queryFn: () => serviceLogsApi.getAll(vehicleId),
        enabled: !!vehicleId,
    });
};

/** Fetch the next upcoming service for a vehicle */
export const useNextService = (vehicleId: string) => {
    return useQuery({
        queryKey: serviceLogKeys.next(vehicleId),
        queryFn: () => serviceLogsApi.getNext(vehicleId),
        enabled: !!vehicleId,
    });
};

/** Create a new service log */
export const useCreateServiceLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CreateServiceLogPayload) =>
            serviceLogsApi.create(vehicleId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.all(vehicleId) });
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.next(vehicleId) });
            queryClient.invalidateQueries({
                queryKey: vehicleKeys.details(vehicleId),
            });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};

/** Update a service log */
export const useUpdateServiceLog = (vehicleId: string, logId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateServiceLogPayload) =>
            serviceLogsApi.update(vehicleId, logId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.all(vehicleId) });
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.next(vehicleId) });
        },
    });
};

/** Delete a service log */
export const useDeleteServiceLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (logId: string) => serviceLogsApi.delete(vehicleId, logId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.all(vehicleId) });
            queryClient.invalidateQueries({ queryKey: serviceLogKeys.next(vehicleId) });
        },
    });
};
