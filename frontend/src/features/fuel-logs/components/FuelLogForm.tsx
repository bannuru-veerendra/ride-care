import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Fuel, Gauge, Loader2, TrendingUp } from "lucide-react";
import { isAxiosError } from "axios";
import { format } from "date-fns";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fuelLogSchema, type FuelLogSchema } from "../schemas";
import type { FuelLog } from "../types";

interface FuelLogFormProps {
    /** Pass a fuel log to pre-fill the form for editing */
    defaultValues?: FuelLog;
    onSubmit: (values: FuelLogSchema) => void;
    isPending: boolean;
    error: Error | null;
}

/**
 * Reusable fuel log form used for both create and edit.
 * Live liters preview from amount ÷ price.
 * Mileage is calculated by the backend from the previous fill-up.
 */
export default function FuelLogForm({
    defaultValues,
    onSubmit,
    isPending,
    error,
}: FuelLogFormProps) {
    const {
        register,
        handleSubmit,
        reset,
        watch,
        formState: { errors },
    } = useForm<FuelLogSchema>({
        resolver: zodResolver(fuelLogSchema),
        defaultValues: {
            date: format(new Date(), "yyyy-MM-dd"),
        },
    });

    const totalCost = watch("total_cost");
    const pricePerLiter = watch("price_per_liter");

    const litersPreview =
        typeof totalCost === "number" &&
        typeof pricePerLiter === "number" &&
        pricePerLiter > 0 &&
        totalCost > 0
            ? totalCost / pricePerLiter
            : null;

    // Pre-fill form when editing
    useEffect(() => {
        if (defaultValues) {
            reset({
                date: defaultValues.date,
                odometer: defaultValues.odometer,
                total_cost: defaultValues.total_cost,
                price_per_liter: defaultValues.price_per_liter,
                notes: defaultValues.notes ?? "",
            });
        }
    }, [defaultValues, reset]);

    const apiError = isAxiosError(error)
        ? error.response?.data?.detail ?? "Something went wrong. Please try again."
        : null;

    const inputClass = "border-white/15 bg-white/5";

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
            {apiError && (
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {apiError}
                </div>
            )}

            {/* Mileage-first preview */}
            <div className="relative overflow-hidden rounded-2xl border border-brand/30 bg-brand/10 px-5 py-5">
                <div
                    aria-hidden
                    className="absolute inset-y-0 left-0 w-1 bg-brand"
                />
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                            <Fuel className="h-3.5 w-3.5" />
                            Liters
                        </p>
                        <p className="font-heading mt-1 text-4xl font-extrabold tracking-wide text-foreground">
                            {litersPreview !== null ? litersPreview.toFixed(2) : "—"}
                        </p>
                    </div>
                    <div>
                        <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                            <TrendingUp className="h-3.5 w-3.5" />
                            Mileage
                        </p>
                        <p className="font-heading mt-1 text-4xl font-extrabold tracking-wide text-brand">
                            {defaultValues?.mileage != null
                                ? defaultValues.mileage
                                : "—"}
                        </p>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">
                            {defaultValues?.mileage != null
                                ? "km/l from this fill"
                                : "Auto-calculated after save"}
                        </p>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <div className="space-y-1.5">
                    <Label htmlFor="date">Date</Label>
                    <Input
                        id="date"
                        type="date"
                        className={inputClass}
                        {...register("date")}
                    />
                    {errors.date && (
                        <p className="text-xs text-destructive">{errors.date.message}</p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="odometer" className="flex items-center gap-1.5">
                        <Gauge className="h-3.5 w-3.5 text-brand" />
                        Odometer reading (km)
                    </Label>
                    <Input
                        id="odometer"
                        type="number"
                        placeholder="12500"
                        className={inputClass}
                        {...register("odometer", { valueAsNumber: true })}
                    />
                    {errors.odometer && (
                        <p className="text-xs text-destructive">{errors.odometer.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                        Used with your last fill to calculate km/l
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                        <Label htmlFor="total_cost">Amount paid (₹)</Label>
                        <Input
                            id="total_cost"
                            type="number"
                            placeholder="500"
                            className={inputClass}
                            {...register("total_cost", { valueAsNumber: true })}
                        />
                        {errors.total_cost && (
                            <p className="text-xs text-destructive">
                                {errors.total_cost.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="price_per_liter">Price / liter (₹)</Label>
                        <Input
                            id="price_per_liter"
                            type="number"
                            placeholder="105"
                            className={inputClass}
                            {...register("price_per_liter", { valueAsNumber: true })}
                        />
                        {errors.price_per_liter && (
                            <p className="text-xs text-destructive">
                                {errors.price_per_liter.message}
                            </p>
                        )}
                    </div>
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="notes">
                        Notes{" "}
                        <span className="text-xs text-muted-foreground">(optional)</span>
                    </Label>
                    <Input
                        id="notes"
                        type="text"
                        placeholder="Full tank, highway ride..."
                        className={inputClass}
                        {...register("notes")}
                    />
                </div>
            </div>

            <Button
                type="submit"
                className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
                disabled={isPending}
            >
                {isPending ? (
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                    </>
                ) : defaultValues ? (
                    "Save changes"
                ) : (
                    "Log fuel & get mileage"
                )}
            </Button>
        </form>
    );
}
