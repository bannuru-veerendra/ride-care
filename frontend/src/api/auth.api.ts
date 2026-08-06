import apiClient from "@/lib/axios";

/**
 * Auth API calls.
 * All endpoints map to the backend /auth routes.
 * Tokens are set as httpOnly cookies by the server — not returned in JSON for SPA login/refresh.
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

export interface SessionResponse {
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

    login: async (payload: LoginPayload): Promise<SessionResponse> => {
        const response = await apiClient.post<SessionResponse>(
            "/auth/login",
            payload
        );
        return response.data;
    },

    refresh: async (): Promise<SessionResponse> => {
        const response = await apiClient.post<SessionResponse>("/auth/refresh", {});
        return response.data;
    },

    logout: async (): Promise<void> => {
        await apiClient.post("/auth/logout", {});
    },
};
