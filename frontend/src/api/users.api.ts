import apiClient from "@/lib/axios";
import type { User } from "@/types";
import type {
    PasswordUpdateSchema,
    ProfileUpdateSchema,
} from "@/features/users/schemas";

/**
 * Users API calls.
 * All endpoints map to the backend /users routes.
 */

export type UpdateProfilePayload = ProfileUpdateSchema;
export type UpdatePasswordPayload = PasswordUpdateSchema;

export const usersApi = {
    getMe: async (): Promise<User> => {
        const { data } = await apiClient.get<User>("/users/me");
        return data;
    },

    updateMe: async (payload: UpdateProfilePayload): Promise<User> => {
        const { data } = await apiClient.patch<User>("/users/me", payload);
        return data;
    },

    updatePassword: async (payload: UpdatePasswordPayload): Promise<void> => {
        await apiClient.patch("/users/me/password", payload);
    },
};
