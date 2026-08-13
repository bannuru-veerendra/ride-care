import { z } from "zod";

import { odometerSchema, pastOrTodayDateSchema } from "@/lib/date";

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
    date: pastOrTodayDateSchema("Fuel log"),
    odometer: odometerSchema,
    total_cost: moneySchema,
    price_per_liter: moneySchema,
    notes: z.string().optional(),
});

export type FuelLogSchema = z.infer<typeof fuelLogSchema>;
