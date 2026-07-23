import apiClient from "@/lib/axios";

/**
 * Users API calls.
 * All endpoints map to the backend /users routes.
 */
export interface UserProfile {
    id: string;
    email: string;
    full_name: string;
}

export interface UpdateProfilePayload {
    full_name?: string;
    email?: string;
}

export interface UpdatePasswordPayload {
    current_password: string;
    new_password: string;
    confirm_password: string;
}

export const usersApi = {
    getMe: async (): Promise<UserProfile> => {
        const { data } = await apiClient.get<UserProfile>("/users/me");
        return data;
    },

    updateMe: async (payload: UpdateProfilePayload): Promise<UserProfile> => {
        const { data } = await apiClient.patch<UserProfile>("/users/me", payload);
        return data;
    },

    updatePassword: async (payload: UpdatePasswordPayload): Promise<void> => {
        await apiClient.patch("/users/me/password", payload);
    },
};
