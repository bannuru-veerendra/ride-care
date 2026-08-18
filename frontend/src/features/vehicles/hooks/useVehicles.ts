import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { vehiclesApi } from "@/api/vehicles.api";
import type { CreateVehiclePayload, UpdateVehiclePayload } from "@/api/vehicles.api";
import { getCursorNextPageParam } from "@/lib/query-client";


/**
 * Query keys for vehicle-related queries
 * Centralized here so invalidation is consistent across the hooks
 */
export const vehicleKeys = {
    all: ["vehicles"] as const,
    infinite: ["vehicles", "infinite"] as const,
    compare: ["vehicles", "compare"] as const,
    details: (id: string) => ["vehicle-detail", id] as const,
    analytics: (id: string) => ["vehicle-analytics", id] as const,
    summary: (id: string) => ["vehicle-summary", id] as const,
};

function invalidateVehicleLists(queryClient: ReturnType<typeof useQueryClient>) {
    queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
}

function removeVehicleScopedQueries(
    queryClient: ReturnType<typeof useQueryClient>,
    id: string
) {
    queryClient.removeQueries({ queryKey: vehicleKeys.details(id) });
    queryClient.removeQueries({ queryKey: vehicleKeys.summary(id) });
    queryClient.removeQueries({ queryKey: vehicleKeys.analytics(id) });
    // Literal prefixes — avoid circular imports with feature hook modules
    queryClient.removeQueries({ queryKey: ["fuel-logs-infinite", id] });
    queryClient.removeQueries({ queryKey: ["service-logs-infinite", id] });
    queryClient.removeQueries({ queryKey: ["documents", id] });
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
        getNextPageParam: getCursorNextPageParam,
    });
};

/** Flat vehicle list for dashboard picker (single page, up to 100) */
export const useVehicles = () => {
    return useQuery({
        queryKey: vehicleKeys.all,
        queryFn: () => vehiclesApi.getAll({ size: 100 }),
    });
};

/** Garage-wide cost and mileage comparison */
export const useVehicleCompare = () => {
    return useQuery({
        queryKey: vehicleKeys.compare,
        queryFn: () => vehiclesApi.compare(),
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
        onSuccess: () => invalidateVehicleLists(queryClient),
    });
};


/** Update an existing vehicle */
export const useUpdateVehicle = (id: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateVehiclePayload) => vehiclesApi.update(id, payload),
        onSuccess: () => {
            invalidateVehicleLists(queryClient);
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
        onSuccess: (_data, id) => {
            invalidateVehicleLists(queryClient);
            removeVehicleScopedQueries(queryClient, id);
        },
    });
};
