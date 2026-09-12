import { z } from "zod";

import { odometerSchema, pastOrTodayDateSchema } from "@/lib/date";
import { positiveDecimal2Schema } from "@/lib/numbers";

/**
 * zod validation schema for fuel log form
 * Mirrors backend validation rules
 */
export const fuelLogSchema = z.object({
    date: pastOrTodayDateSchema("Fuel log"),
    odometer: odometerSchema,
    total_cost: positiveDecimal2Schema,
    price_per_liter: positiveDecimal2Schema,
    notes: z.string().optional(),
});

export type FuelLogSchema = z.infer<typeof fuelLogSchema>;
