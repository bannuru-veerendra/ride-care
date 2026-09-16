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
    reminders_muted: boolean;
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
    display_label: string;
    identifier: string | null;
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
    reminders_muted?: boolean;
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
    service_spend: number;
    service_count: number;
    combined_spend: number;
    km_driven: number;
    cost_per_km: number | null;
    fuel_cost_per_km: number | null;
    service_cost_per_km: number | null;
}

export interface VehicleCompareItem {
    vehicle_id: string;
    brand: string;
    vehicle_name: string;
    year: number;
    current_odometer: number;
    km_driven: number;
    avg_mileage: number | null;
    fuel_spend: number;
    service_spend: number;
    combined_spend: number;
    cost_per_km: number | null;
    fill_up_count: number;
    service_count: number;
}

export interface VehicleCompareResponse {
    items: VehicleCompareItem[];
}

export type HealthUrgency = "critical" | "high" | "medium" | "low" | "none";
export type HealthConfidence = "high" | "medium" | "low" | "insufficient";
export type HealthHrefHint =
    | "service"
    | "documents"
    | "fuel"
    | "analytics"
    | "vehicle";

export interface HealthEvidence {
    label: string;
    value: string;
}

export interface HealthSignal {
    id: string;
    kind: string;
    urgency: HealthUrgency;
    title: string;
    detail: string;
    confidence: HealthConfidence;
    evidence: HealthEvidence[];
    href_hint: HealthHrefHint | null;
}

export interface RecommendedAction {
    kind: string;
    title: string;
    reason: string;
    urgency: HealthUrgency;
    href_hint: HealthHrefHint;
    confidence: HealthConfidence;
}

export interface ServicePrediction {
    source: "rider_schedule" | "catalog_estimate" | "insufficient";
    predicted_date: string | null;
    predicted_odometer: number | null;
    days_until: number | null;
    km_until: number | null;
    riding_rate_km_per_day: number | null;
    detail: string;
    matched_task: string | null;
}

export interface MileageHealth {
    trend: "up" | "down" | "flat" | "insufficient";
    recent_avg: number | null;
    earlier_avg: number | null;
    delta: number | null;
    sample_n: number;
    detail: string;
}

export interface CostHealth {
    cost_per_km: number | null;
    km_driven: number;
    fill_ups: number;
    confidence: HealthConfidence;
    detail: string;
}

export interface VehicleHealth {
    vehicle_id: string;
    reminders_muted: boolean;
    recommended_action: RecommendedAction | null;
    signals: HealthSignal[];
    service_prediction: ServicePrediction;
    mileage: MileageHealth;
    cost: CostHealth;
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
    getHealth: async (id: string): Promise<VehicleHealth> => {
        const { data } = await apiClient.get(`/vehicles/${id}/health`);
        return data;
    },
    compare: async (): Promise<VehicleCompareResponse> => {
        const { data } = await apiClient.get("/vehicles/compare");
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
