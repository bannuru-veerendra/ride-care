import { z } from "zod";

import { odometerSchema, pastOrTodayDateSchema } from "@/lib/date";
import { positiveDecimal2Schema } from "@/lib/numbers";

/**
 * Common service items users can pick from.
 * Users can also type custom ones.
 */
export const COMMON_SERVICES = [
    "Engine Oil",
    "Oil Filter",
    "Air Filter",
    "Spark Plug",
    "Chain Lubrication",
    "Chain Sprocket",
    "Brake Fluid",
    "Brake Pads",
    "Tyre Change",
    "General Service",
];

/**
 * Zod validation schema for service log form.
 * Mirrors backend validation rules.
 */
export const serviceLogSchema = z.object({
    date: pastOrTodayDateSchema("Service log"),
    odometer: odometerSchema,
    service_center: z.string().optional(),
    total_cost: positiveDecimal2Schema,
    services_done: z
        .array(z.string())
        .min(1, { message: "Select at least one service" }),
    next_service_date: z.string().optional(),
    next_service_odometer: positiveDecimal2Schema.optional(),
    notes: z.string().optional(),
});

export type ServiceLogSchema = z.infer<typeof serviceLogSchema>;
