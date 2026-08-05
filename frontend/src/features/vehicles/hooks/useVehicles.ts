import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { vehiclesApi } from "@/api/vehicles.api";
import type { CreateVehiclePayload, UpdateVehiclePayload } from "@/api/vehicles.api";


/**
 * Query keys for vehicle-related queries
 * Centralized here so invalidation is consistent across the hooks
 */
export const vehicleKeys = {
    all: ["vehicles"] as const,
    details: (id: string) => ["vehicle", id] as const,
    analytics: (id: string) => ["vehicle-analytics", id] as const,
}

/** Fetch all vehicles for the current user */
export const useVehicles = () => {
    return useQuery({
        queryKey: vehicleKeys.all,
        queryFn: () => vehiclesApi.getAll(),
    });
};


/** Fetch a single vehicle by ID */
export const useVehicle = (id: string) => {
    return useQuery({
        queryKey: vehicleKeys.details(id),
        queryFn: () => vehiclesApi.getById(id),
        enabled: !!id,
    });
};


/** Fetch analytics aggregates for a vehicle */
export const useVehicleAnalytics = (id: string) => {
    return useQuery({
        queryKey: vehicleKeys.analytics(id),
        queryFn: () => vehiclesApi.getAnalytics(id),
        enabled: !!id,
    });
};


/** Create a new vehicle */
export const useCreateVehicle = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (payload: CreateVehiclePayload) => vehiclesApi.create(payload),
        onSuccess: () => {
            // Refresh the vehicles list after creating a new vehicle
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};


/** Update an existing vehicle */
export const useUpdateVehicle = (id: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateVehiclePayload) => vehiclesApi.update(id, payload),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.details(id) });
        },
    });
};


/** Delete a vehicle */
export const useDeleteVehicle = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (id: string) => vehiclesApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
        },
    });
};
