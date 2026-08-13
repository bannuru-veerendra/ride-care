import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import FormErrorBanner from "@/components/common/FormErrorBanner";
import FormSubmitButton from "@/components/common/FormSubmitButton";
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
    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<VehicleSchema>({
        resolver: zodResolver(vehicleSchema),
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
                        placeholder="12000"
                        {...register("baseline_odometer", { valueAsNumber: true })}
                    />
                    {errors.baseline_odometer && (
                        <p className="text-destructive text-xs">
                            {errors.baseline_odometer.message}
                        </p>
                    )}
                </div>
            </div>

            <FormSubmitButton
                isPending={isPending}
                isEdit={!!defaultValues}
                createLabel="Add vehicle"
                className="w-full"
            />
        </form>
    );
}
