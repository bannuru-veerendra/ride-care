import { z } from "zod";

import { appTodayISO } from "@/lib/date";

/** Accept positive numbers with at most 2 decimal places; normalize to 2 dp. */
const moneySchema = z
    .number({ error: "Must be a number" })
    .positive({ message: "Must be greater than 0" })
    .refine(
        (value) => Math.abs(value * 100 - Math.round(value * 100)) < 1e-6,
        { message: "Use up to 2 decimal places" }
    )
    .transform((value) => Math.round(value * 100) / 100);

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
        .positive({ message: "Odometer must be greater than 0" })
        .int({ message: "Odometer must be a whole number (km)" }),
    total_cost: moneySchema,
    price_per_liter: moneySchema,
    notes: z.string().optional(),
});

export type FuelLogSchema = z.infer<typeof fuelLogSchema>;
