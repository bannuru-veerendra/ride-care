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

export interface ServiceReminder {
    status: "ok" | "soon" | "overdue" | "none";
    days_until: number | null;
    km_until: number | null;
    next_service_date: string | null;
    next_service_odometer: number | null;
}

export interface DocumentReminder {
    id: string;
    document_type: string;
    expiry_date: string;
    days_until: number;
    status: "ok" | "soon" | "expired";
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
    service_reminder: ServiceReminder;
    document_reminders: DocumentReminder[];
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
    getAll: async (params?: {
        cursor?: string;
        size?: number;
    }): Promise<CursorPage<Vehicle>> => {
        const { data } = await apiClient.get("/vehicles/", { params });
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
