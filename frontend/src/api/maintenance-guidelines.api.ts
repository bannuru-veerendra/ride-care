import apiClient from "@/lib/axios";

/**
 * Maintenance guidelines API calls.
 * Data served from JSON file on backend — no DB query.
 */

export type Severity = "critical" | "high" | "medium" | "low";

export interface MaintenanceGuideline {
    id: string;
    component: string;
    task: string;
    interval_km: number | null;
    interval_months: number | null;
    description: string;
    severity: Severity;
    sort_order: number;
}

export const maintenanceGuidelinesApi = {
    getAll: async (params?: {
        severity?: Severity;
        component?: string;
    }): Promise<MaintenanceGuideline[]> => {
        const { data } = await apiClient.get("/maintenance-guidelines/", {
            params,
        });
        return data;
    },

    getComponents: async (): Promise<string[]> => {
        const { data } = await apiClient.get(
            "/maintenance-guidelines/components"
        );
        return data;
    },
};
