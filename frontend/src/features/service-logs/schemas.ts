import { z } from "zod";

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
    date: z.string().min(1, { message: "Date is required" }),
    odometer: z
        .number({ error: "Odometer must be a number" })
        .min(1, { message: "Odometer must be greater than 0" }),
    service_center: z.string().optional(),
    total_cost: z
        .number({ error: "Cost must be a number" })
        .min(1, { message: "Cost must be greater than 0" }),
    services_done: z
        .array(z.string())
        .min(1, { message: "Select at least one service" }),
    next_service_date: z.string().optional(),
    next_service_odometer: z.number().optional(),
    notes: z.string().optional(),
});

export type ServiceLogSchema = z.infer<typeof serviceLogSchema>;
