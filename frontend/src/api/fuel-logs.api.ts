import apiClient from "@/lib/axios";
import type { CursorPage } from "@/types";

/**
 * Fuel log API calls
 * All endpoints map to the backend /fuel_logs routes
 * vehicle_id is passed as a query parameter
 */

export interface FuelLog {
    id: string;
    vehicle_id: string;
    date: string;
    odometer: number;
    total_cost: number;
    price_per_liter: number;
    liters: number;
    mileage: number | null;
    notes: string | null;
}


export interface CreateFuelLogPayload {
    date: string;
    odometer: number;
    total_cost: number;
    price_per_liter: number;
    notes?: string;
}

export interface UpdateFuelLogPayload {
    date?: string;
    odometer?: number;
    total_cost?: number;
    price_per_liter?: number;
    notes?: string;
}

export const fuelLogsApi = {
    getAll: async (vehicleId: string): Promise<CursorPage<FuelLog>> => {
        const { data } = await apiClient.get("/fuel_logs/", {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },
    getById: async (vehicleId: string, logId: string): Promise<FuelLog> => {
        const { data } = await apiClient.get(`/fuel_logs/${logId}`, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },
    create: async (vehicleId: string, payload: CreateFuelLogPayload): Promise<FuelLog> => {
        const { data } = await apiClient.post("/fuel_logs/", payload, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },
    update: async (
        vehicleId: string,
        logId: string,
        payload: UpdateFuelLogPayload
    ): Promise<FuelLog> => {
        const { data } = await apiClient.patch(`/fuel_logs/${logId}`, payload, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },
    delete: async (vehicleId: string, logId: string): Promise<void> => {
        await apiClient.delete(`/fuel_logs/${logId}`, {
            params: { vehicle_id: vehicleId },
        });
    }
}

export default fuelLogsApi;
