import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import FormErrorBanner from "@/components/common/FormErrorBanner";
import FormSubmitButton from "@/components/common/FormSubmitButton";
import { cn } from "@/lib/utils";
import { vehicleSchema, type VehicleSchema } from "../schemas";
import type { Vehicle } from "../types";

interface VehicleFormProps {
    /** Pass a vehicle to pre-fill the form for editing */
    defaultValues?: Vehicle;
    onSubmit: (values: VehicleSchema) => void;
    isPending: boolean;
    error: Error | null;
}

/**
 * Reusable vehicle form used for both create and edit.
 * Pre-fills fields when defaultValues is provided (edit mode).
 */
export default function VehicleForm({
    defaultValues,
    onSubmit,
    isPending,
    error,
}: VehicleFormProps) {
    const isEdit = !!defaultValues;
    const {
        register,
        handleSubmit,
        reset,
        control,
        formState: { errors },
    } = useForm<VehicleSchema>({
        resolver: zodResolver(vehicleSchema),
        reValidateMode: "onBlur",
        defaultValues: {
            reminders_muted: false,
        },
    });

    // Pre-fill form when editing
    useEffect(() => {
        if (defaultValues) {
            reset({
                brand: defaultValues.brand,
                vehicle_name: defaultValues.vehicle_name,
                year: defaultValues.year,
                registration_number: defaultValues.registration_number,
                baseline_odometer: defaultValues.baseline_odometer,
                reminders_muted: defaultValues.reminders_muted ?? false,
            });
        }
    }, [defaultValues, reset]);

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormErrorBanner error={error} />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                    <Label htmlFor="brand">Brand</Label>
                    <Input id="brand" placeholder="Yamaha" {...register("brand")} />
                    {errors.brand && (
                        <p className="text-destructive text-xs">{errors.brand.message}</p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="vehicle_name">Vehicle name</Label>
                    <Input
                        id="vehicle_name"
                        placeholder="R15 V4"
                        {...register("vehicle_name")}
                    />
                    {errors.vehicle_name && (
                        <p className="text-destructive text-xs">
                            {errors.vehicle_name.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="year">Year</Label>
                    <Input
                        id="year"
                        type="number"
                        placeholder="2024"
                        {...register("year", { valueAsNumber: true })}
                    />
                    {errors.year && (
                        <p className="text-destructive text-xs">{errors.year.message}</p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="registration_number">Registration number</Label>
                    <Input
                        id="registration_number"
                        placeholder="AP12SN3456"
                        {...register("registration_number")}
                    />
                    {errors.registration_number && (
                        <p className="text-destructive text-xs">
                            {errors.registration_number.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5 sm:col-span-2">
                    <Label htmlFor="baseline_odometer">Baseline odometer (km)</Label>
                    <Input
                        id="baseline_odometer"
                        type="number"
                        inputMode="decimal"
                        step="0.01"
                        placeholder="12000.00"
                        {...register("baseline_odometer", { valueAsNumber: true })}
                    />
                    {errors.baseline_odometer && (
                        <p className="text-destructive text-xs">
                            {errors.baseline_odometer.message}
                        </p>
                    )}
                </div>
            </div>

            {isEdit && (
                <Controller
                    name="reminders_muted"
                    control={control}
                    render={({ field }) => (
                        <div className="flex items-start justify-between gap-4 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
                            <div className="min-w-0">
                                <Label
                                    htmlFor="reminders_muted"
                                    className="cursor-pointer text-sm font-medium"
                                >
                                    Reminders off — history kept
                                </Label>
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                    Skip dashboard and email reminders for this bike.
                                    Fuel, service, and documents stay available.
                                </p>
                            </div>
                            <button
                                id="reminders_muted"
                                type="button"
                                role="switch"
                                aria-checked={field.value}
                                disabled={isPending}
                                onClick={() => field.onChange(!field.value)}
                                className={cn(
                                    "relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition-colors",
                                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60",
                                    "disabled:cursor-not-allowed disabled:opacity-50",
                                    field.value ? "bg-brand" : "bg-white/15"
                                )}
                            >
                                <span
                                    aria-hidden
                                    className={cn(
                                        "absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform",
                                        field.value && "translate-x-5"
                                    )}
                                />
                            </button>
                        </div>
                    )}
                />
            )}

            <FormSubmitButton
                isPending={isPending}
                isEdit={isEdit}
                createLabel="Add vehicle"
                className="w-full"
            />
        </form>
    );
}
