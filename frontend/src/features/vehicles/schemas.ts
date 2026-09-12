import { z } from "zod";

import { nonNegativeDecimal2Schema } from "@/lib/numbers";

const currentYear = new Date().getFullYear();

/**
 * zod validation schema for vehicle form
 * Mirrors backend validation rules
 */

export const vehicleSchema = z.object({
    brand: z.string().min(1, { message: "Brand is required" }),
    vehicle_name: z.string().min(1, { message: "Vehicle name is required" }),
    year: z
        .number({ error: "Year must be a number" })
        .min(1900, { message: "Year must be after 1900" })
        .max(currentYear, { message: `Year cannot exceed ${currentYear}` }),
    registration_number: z.string().min(1, { message: "Registration number is required" }),
    baseline_odometer: nonNegativeDecimal2Schema,
    reminders_muted: z.boolean().default(false),
});

export type VehicleSchema = z.infer<typeof vehicleSchema>;
