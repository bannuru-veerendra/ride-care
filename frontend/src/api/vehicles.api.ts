import apiClient from "@/lib/axios";

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
    current_odometer: number;
}


export interface CreateVehiclePayload {
    brand: string;
    vehicle_name: string;
    year: number;
    registration_number: string;
    current_odometer: number;
}

export interface UpdateVehiclePayload {
    brand?: string;
    vehicle_name?: string;
    year?: number;
    registration_number?: string;
    current_odometer?: number;
}

export const vehiclesApi = {
    getAll: async (): Promise<Vehicle[]> => {
        const { data } = await apiClient.get("/vehicles/");
        return data;
    },
    getById: async (id: string): Promise<Vehicle> => {
        const { data } = await apiClient.get(`/vehicles/${id}`);
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
