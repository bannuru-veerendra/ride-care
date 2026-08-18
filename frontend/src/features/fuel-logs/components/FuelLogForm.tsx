import { useEffect, useRef, type ChangeEvent } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Fuel, Gauge, TrendingUp } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import FormErrorBanner from "@/components/common/FormErrorBanner";
import FormSubmitButton from "@/components/common/FormSubmitButton";
import { fuelLogSchema, type FuelLogSchema } from "../schemas";
import type { FuelLog } from "../types";
import { appTodayISO } from "@/lib/date";

interface FuelLogFormProps {
    /** Pass a fuel log to pre-fill the form for editing */
    defaultValues?: FuelLog;
    onSubmit: (values: FuelLogSchema) => void;
    isPending: boolean;
    error: Error | null;
}

function readNumber(value: string): number | undefined {
    if (value === "") return undefined;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
}

function formatLiters(cost: number | undefined, price: number | undefined): string {
    if (
        typeof cost === "number" &&
        typeof price === "number" &&
        price > 0 &&
        cost > 0
    ) {
        return (cost / price).toFixed(2);
    }
    return "—";
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
    const litersRef = useRef<HTMLSpanElement>(null);
    const costRef = useRef<number | undefined>(defaultValues?.total_cost);
    const priceRef = useRef<number | undefined>(defaultValues?.price_per_liter);

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<FuelLogSchema>({
        resolver: zodResolver(fuelLogSchema),
        reValidateMode: "onBlur",
        defaultValues: {
            date: appTodayISO(),
        },
    });

    const paintLiters = () => {
        if (litersRef.current) {
            litersRef.current.textContent = formatLiters(
                costRef.current,
                priceRef.current
            );
        }
    };

    // Pre-fill form when editing
    useEffect(() => {
        if (!defaultValues) return;
        costRef.current = defaultValues.total_cost;
        priceRef.current = defaultValues.price_per_liter;
        reset({
            date: defaultValues.date,
            odometer: defaultValues.odometer,
            total_cost: defaultValues.total_cost,
            price_per_liter: defaultValues.price_per_liter,
            notes: defaultValues.notes ?? "",
        });
        if (litersRef.current) {
            litersRef.current.textContent = formatLiters(
                defaultValues.total_cost,
                defaultValues.price_per_liter
            );
        }
    }, [defaultValues, reset]);

    const totalCostReg = register("total_cost", { valueAsNumber: true });
    const priceReg = register("price_per_liter", { valueAsNumber: true });

    const onMoneyChange =
        (
            field: typeof totalCostReg | typeof priceReg,
            target: typeof costRef | typeof priceRef
        ) =>
        (event: ChangeEvent<HTMLInputElement>) => {
            void field.onChange(event);
            target.current = readNumber(event.currentTarget.value);
            paintLiters();
        };

    const inputClass = "border-white/15 bg-white/5";

    return (
        <form
            onSubmit={handleSubmit(onSubmit)}
            className="flex flex-col gap-6"
            noValidate
        >
            <FormErrorBanner error={error} />

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
                            <span ref={litersRef}>
                                {formatLiters(
                                    defaultValues?.total_cost,
                                    defaultValues?.price_per_liter
                                )}
                            </span>
                        </p>
                    </div>
                    <div>
                        <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                            <TrendingUp className="h-3.5 w-3.5" />
                            Mileage
                        </p>
                        <p className="font-heading mt-1 text-4xl font-extrabold tracking-wide text-brand">
                            {defaultValues?.mileage != null
                                ? defaultValues.mileage.toFixed(1)
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
                        max={appTodayISO()}
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
                        inputMode="numeric"
                        step={1}
                        min={1}
                        placeholder="12500"
                        className={inputClass}
                        {...register("odometer", { valueAsNumber: true })}
                    />
                    {errors.odometer && (
                        <p className="text-xs text-destructive">{errors.odometer.message}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                        Whole kilometers — used with your last fill to calculate km/l
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                        <Label htmlFor="total_cost">Amount paid (₹)</Label>
                        <Input
                            id="total_cost"
                            type="number"
                            inputMode="decimal"
                            step="0.01"
                            min={0.01}
                            placeholder="500.00"
                            className={inputClass}
                            {...totalCostReg}
                            onChange={onMoneyChange(totalCostReg, costRef)}
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
                            inputMode="decimal"
                            step="0.01"
                            min={0.01}
                            placeholder="105.00"
                            className={inputClass}
                            {...priceReg}
                            onChange={onMoneyChange(priceReg, priceRef)}
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

            <FormSubmitButton
                isPending={isPending}
                isEdit={!!defaultValues}
                createLabel="Log fuel & get mileage"
                className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
            />
        </form>
    );
}
