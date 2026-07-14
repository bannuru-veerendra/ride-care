import apiClient from "@/lib/axios";

/**
 * Service log API calls.
 * All endpoints map to the backend /service_logs routes.
 * vehicle_id is passed as a query parameter.
 */

export interface ServiceLog {
    id: string;
    vehicle_id: string;
    date: string;
    odometer: number;
    service_center: string | null;
    total_cost: number;
    services_done: string[];
    next_service_date: string | null;
    next_service_odometer: number | null;
    notes: string | null;
}

export interface CreateServiceLogPayload {
    date: string;
    odometer: number;
    service_center?: string;
    total_cost: number;
    services_done: string[];
    next_service_date?: string;
    next_service_odometer?: number;
    notes?: string;
}

export interface UpdateServiceLogPayload {
    date?: string;
    odometer?: number;
    service_center?: string;
    total_cost?: number;
    services_done?: string[];
    next_service_date?: string;
    next_service_odometer?: number;
    notes?: string;
}

export const serviceLogsApi = {
    getAll: async (vehicleId: string): Promise<ServiceLog[]> => {
        const { data } = await apiClient.get("/service_logs/", {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    getNext: async (vehicleId: string): Promise<ServiceLog | null> => {
        const { data } = await apiClient.get("/service_logs/next", {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    getById: async (vehicleId: string, logId: string): Promise<ServiceLog> => {
        const { data } = await apiClient.get(`/service_logs/${logId}`, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    create: async (
        vehicleId: string,
        payload: CreateServiceLogPayload
    ): Promise<ServiceLog> => {
        const { data } = await apiClient.post("/service_logs/", payload, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    update: async (
        vehicleId: string,
        logId: string,
        payload: UpdateServiceLogPayload
    ): Promise<ServiceLog> => {
        const { data } = await apiClient.patch(`/service_logs/${logId}`, payload, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },

    delete: async (vehicleId: string, logId: string): Promise<void> => {
        await apiClient.delete(`/service_logs/${logId}`, {
            params: { vehicle_id: vehicleId },
        });
    },
};

export default serviceLogsApi;
