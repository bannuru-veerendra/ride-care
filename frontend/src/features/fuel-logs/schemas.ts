import { z } from "zod";

import { appTodayISO } from "@/lib/date";

/**
 * zod validation schema for fuel log form
 * Mirrors backend validation rules
 */

export const fuelLogSchema = z.object({
    date: z
        .string()
        .min(1, { message: "Date is required" })
        .refine((value) => value <= appTodayISO(), {
            message: "Fuel log date cannot be in the future",
        }),
    odometer: z
        .number({ error: "Odometer must be a number" })
        .min(1, { message: "Odometer must be greater than 0" }),
    total_cost: z
        .number({ error: "Amount must be a number" })
        .min(1, { message: "Amount must be greater than 0" }),
    price_per_liter: z
        .number({ error: "Price must be a number" })
        .min(1, { message: "Price per liter must be greater than 0" }),
    notes: z.string().optional(),
});

export type FuelLogSchema = z.infer<typeof fuelLogSchema>;
