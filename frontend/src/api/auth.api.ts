import apiClient from "@/lib/axios";

/**
 * Auth API calls.
 * All endpoints map to the backend /auth routes.
 */
export interface RegisterPayload {
    email: string;
    full_name: string;
    password: string;
}

export interface LoginPayload {
    email: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface UserResponse {
    id: string;
    email: string;
    full_name: string;
}

export const authApi = {
    register: async (payload: RegisterPayload): Promise<UserResponse> => {
        const response = await apiClient.post<UserResponse>(
            "/auth/register",
            payload
        );
        return response.data;
    },

    login: async (payload: LoginPayload): Promise<AuthResponse> => {
        const response = await apiClient.post<AuthResponse>(
            "/auth/login",
            payload
        );
        return response.data;
    },

    refresh: async (refreshToken: string): Promise<AuthResponse> => {
        const response = await apiClient.post<AuthResponse>("/auth/refresh", {
            refresh_token: refreshToken,
        });
        return response.data;
    },

    logout: async (refreshToken: string): Promise<void> => {
        await apiClient.post("/auth/logout", {
            refresh_token: refreshToken,
        });
    },
};
