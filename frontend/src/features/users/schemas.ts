import { z } from "zod";

/**
 * Lightweight client checks only (required fields / confirm match).
 * Password strength, email normalization, and name rules live on the backend.
 */
export const profileUpdateSchema = z.object({
    full_name: z.string().min(1, "Full name is required"),
    email: z.string().min(1, "Email is required"),
});

export const passwordUpdateSchema = z
    .object({
        current_password: z.string().min(1, "Current password is required"),
        new_password: z.string().min(1, "New password is required"),
        confirm_password: z.string().min(1, "Please confirm your new password"),
    })
    .refine((data) => data.new_password === data.confirm_password, {
        path: ["confirm_password"],
        message: "Passwords do not match",
    });

export type ProfileUpdateSchema = z.infer<typeof profileUpdateSchema>;
export type PasswordUpdateSchema = z.infer<typeof passwordUpdateSchema>;
