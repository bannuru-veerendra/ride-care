import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { vehiclesApi } from "@/api/vehicles.api";
import type { CreateVehiclePayload, UpdateVehiclePayload } from "@/api/vehicles.api";


/**
 * Query keys for vehicle-related queries
 * Centralized here so invalidation is consistent across the hooks
 */
export const vehicleKeys = {
    all: ["vehicles"] as const,
    infinite: ["vehicles", "infinite"] as const,
    details: (id: string) => ["vehicle-detail", id] as const,
    analytics: (id: string) => ["vehicle-analytics", id] as const,
    summary: (id: string) => ["vehicle-summary", id] as const,
}

/** Paginated vehicles with Load more support for the garage */
export const useInfiniteVehicles = () => {
    return useInfiniteQuery({
        queryKey: vehicleKeys.infinite,
        queryFn: ({ pageParam }) =>
            vehiclesApi.getAll({
                cursor: pageParam,
                size: 20,
            }),
        initialPageParam: undefined as string | undefined,
        getNextPageParam: (lastPage) =>
            lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined,
    });
};

/** @deprecated Prefer useInfiniteVehicles — kept for single-page consumers that auto-load */
export const useVehicles = () => {
    return useQuery({
        queryKey: vehicleKeys.all,
        queryFn: () => vehiclesApi.getAll({ size: 100 }),
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

/** Fetch dashboard aggregations for a vehicle */
export const useVehicleSummary = (id: string) => {
    return useQuery({
        queryKey: vehicleKeys.summary(id),
        queryFn: () => vehiclesApi.getSummary(id),
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
            queryClient.invalidateQueries({ queryKey: vehicleKeys.summary(id) });
            queryClient.invalidateQueries({ queryKey: vehicleKeys.analytics(id) });
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
