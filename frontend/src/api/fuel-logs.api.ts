import apiClient from "@/lib/axios";
import type { CursorPage } from "@/types";
import type { FuelLogSchema } from "@/features/fuel-logs/schemas";

/**
 * Fuel log API calls.
 * All endpoints map to the backend /fuel_logs routes.
 * vehicle_id is passed as a query parameter.
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

export type CreateFuelLogPayload = FuelLogSchema;
export type UpdateFuelLogPayload = Partial<FuelLogSchema>;

export const fuelLogsApi = {
    getAll: async (
        vehicleId: string,
        params?: { cursor?: string; size?: number }
    ): Promise<CursorPage<FuelLog>> => {
        const { data } = await apiClient.get("/fuel_logs/", {
            params: { vehicle_id: vehicleId, ...params },
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
    },
    exportCsv: async (vehicleId: string): Promise<Blob> => {
        const { data } = await apiClient.get("/fuel_logs/export", {
            params: { vehicle_id: vehicleId },
            responseType: "blob",
        });
        return data;
    },
    importCsv: async (
        vehicleId: string,
        file: File
    ): Promise<{ imported: number; errors: { row: number; message: string }[] }> => {
        const formData = new FormData();
        formData.append("file", file);
        const { data } = await apiClient.post("/fuel_logs/import", formData, {
            params: { vehicle_id: vehicleId },
        });
        return data;
    },
};

