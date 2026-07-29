import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fuelLogsApi } from "@/api/fuel-logs.api";
import type { CreateFuelLogPayload, UpdateFuelLogPayload } from "@/api/fuel-logs.api";
import { vehicleKeys } from "@/features/vehicles/hooks/useVehicles";


/**
 * Query keys for fuel log queries
 * Scoped under vehicle ID so invalidation is precise
 */
export const fuelLogKeys = {
    all: (vehicleId: string) => ["fuel-logs", vehicleId] as const,
    details: (vehicleId: string, logId: string) =>
        ["fuel-logs", vehicleId, logId] as const,
}

/** Fetch all fuel logs for a vehicle */
export const useFuelLogs = (vehicleId: string) => {
    return useQuery({
        queryKey: fuelLogKeys.all(vehicleId),
        queryFn: () => fuelLogsApi.getAll(vehicleId),
        enabled: !!vehicleId,
    });
};


/** Create a new fuel log */
export const useCreateFuelLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: CreateFuelLogPayload) =>
            fuelLogsApi.create(vehicleId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: fuelLogKeys.all(vehicleId) });
            // Also refresh the vehicle to reflect updated odometer
            queryClient.invalidateQueries({
                queryKey: vehicleKeys.details(vehicleId),
            });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};


/** Update a fuel log */
export const useUpdateFuelLog = (vehicleId: string, logId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateFuelLogPayload) =>
            fuelLogsApi.update(vehicleId, logId, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: fuelLogKeys.all(vehicleId) });
            queryClient.invalidateQueries({
                queryKey: vehicleKeys.details(vehicleId),
            });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};


/** Delete a fuel log */
export const useDeleteFuelLog = (vehicleId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (logId: string) => fuelLogsApi.delete(vehicleId, logId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: fuelLogKeys.all(vehicleId) });
            queryClient.invalidateQueries({
                queryKey: vehicleKeys.details(vehicleId),
            });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(vehicleId) });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};
