import apiClient from "@/lib/axios";
import type { CursorPage } from "@/types";
import type { FuelLog } from "@/features/fuel-logs/types";
import type { ServiceLog } from "@/features/service-logs/types";

/**
 * Vehicles API calls
 * All endpoints map to the backend /vehicles route
 */

export interface Vehicle {
    id: string;
    owner_id: string;
    brand: string;
    vehicle_name: string;
    year: number;
    registration_number: string;
    baseline_odometer: number;
    current_odometer: number;
}

export interface VehicleSummary {
    vehicle_id: string;
    fuel_log_count: number;
    average_mileage: number | null;
    this_month_spend: number;
    last_month_spend: number;
    this_month_mileage: number | null;
    last_month_mileage: number | null;
    recent_filled_month_mileage: number | null;
    prior_filled_month_mileage: number | null;
    recent_filled_month_label: string | null;
    prior_filled_month_label: string | null;
    recent_fuel_logs: FuelLog[];
    next_service: ServiceLog | null;
}


export interface CreateVehiclePayload {
    brand: string;
    vehicle_name: string;
    year: number;
    registration_number: string;
    baseline_odometer: number;
}

export interface UpdateVehiclePayload {
    brand?: string;
    vehicle_name?: string;
    year?: number;
    registration_number?: string;
    baseline_odometer?: number;
}

export interface MileageTrendPoint {
    date: string;
    date_label: string;
    mileage: number;
    odometer: number;
}

export interface MonthlySpendPoint {
    month: string;
    year_month: string;
    spend: number;
    liters: number;
}

export interface VehicleAnalytics {
    vehicle_id: string;
    total_spend: number;
    total_liters: number;
    avg_mileage: number | null;
    best_mileage: number | null;
    worst_mileage: number | null;
    total_fill_ups: number;
    mileage_trend: MileageTrendPoint[];
    monthly_spend: MonthlySpendPoint[];
}

export const vehiclesApi = {
    getAll: async (): Promise<CursorPage<Vehicle>> => {
        const { data } = await apiClient.get("/vehicles/");
        return data;
    },
    getById: async (id: string): Promise<Vehicle> => {
        const { data } = await apiClient.get(`/vehicles/${id}`);
        return data;
    },
    getAnalytics: async (id: string): Promise<VehicleAnalytics> => {
        const { data } = await apiClient.get(`/vehicles/${id}/analytics`);
        return data;
    },
    getSummary: async (id: string): Promise<VehicleSummary> => {
        const { data } = await apiClient.get(`/vehicles/${id}/summary`);
        return data;
    },
    create: async (payload: CreateVehiclePayload): Promise<Vehicle> => {
        const { data } = await apiClient.post("/vehicles/", payload);
        return data;
    },
    update: async (id: string, payload: UpdateVehiclePayload): Promise<Vehicle> => {
        const { data } = await apiClient.patch(`/vehicles/${id}`, payload);
        return data;
    },
    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/vehicles/${id}`);
    }
}

export default vehiclesApi;
