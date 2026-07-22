import { z } from "zod";

/**
 * Lightweight client checks only (required fields / confirm match).
 * Password strength, email normalization, and name rules live on the backend.
 */
export const loginSchema = z.object({
    email: z.string().min(1, "Email is required"),
    password: z.string().min(1, "Password is required"),
});

export const registerSchema = z
    .object({
        email: z.string().min(1, "Email is required"),
        full_name: z.string().min(1, "Full name is required"),
        password: z.string().min(1, "Password is required"),
        confirm_password: z.string().min(1, "Please confirm your password"),
    })
    .refine((data) => data.password === data.confirm_password, {
        path: ["confirm_password"],
        message: "Passwords do not match",
    });

export type LoginSchema = z.infer<typeof loginSchema>;
export type RegisterSchema = z.infer<typeof registerSchema>;
