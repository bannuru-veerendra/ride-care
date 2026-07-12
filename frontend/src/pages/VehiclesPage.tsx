import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";

import VehicleCard from "@/features/vehicles/components/VehicleCard";
import VehicleForm from "@/features/vehicles/components/VehicleForm";
import {
    useVehicles,
    useCreateVehicle,
    useUpdateVehicle,
    useDeleteVehicle,
} from "@/features/vehicles/hooks/useVehicles";
import type { Vehicle } from "@/features/vehicles/types";
import type { VehicleSchema } from "@/features/vehicles/schemas";

/**
 * Vehicles list — the rider's garage.
 */
export default function VehiclesPage() {
    const [sheetOpen, setSheetOpen] = useState(false);
    const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);

    const { data: vehicles, isLoading } = useVehicles();
    const createVehicle = useCreateVehicle();
    const updateVehicle = useUpdateVehicle(editingVehicle?.id ?? "");
    const deleteVehicle = useDeleteVehicle();

    const handleSubmit = (values: VehicleSchema) => {
        if (editingVehicle) {
            updateVehicle.mutate(values, {
                onSuccess: () => {
                    toast.success("Vehicle updated successfully");
                    setSheetOpen(false);
                    setEditingVehicle(null);
                },
            });
        } else {
            createVehicle.mutate(values, {
                onSuccess: () => {
                    toast.success("Vehicle added successfully");
                    setSheetOpen(false);
                },
            });
        }
    };

    const handleEdit = (vehicle: Vehicle) => {
        setEditingVehicle(vehicle);
        setSheetOpen(true);
    };

    const handleDelete = (id: string) => {
        if (!confirm("Are you sure you want to delete this vehicle?")) return;
        deleteVehicle.mutate(id, {
            onSuccess: () => toast.success("Vehicle deleted"),
            onError: () => toast.error("Failed to delete vehicle"),
        });
    };

    const handleSheetOpenChange = (open: boolean) => {
        setSheetOpen(open);
        if (!open) setEditingVehicle(null);
    };

    return (
        <div className="animate-fade-up space-y-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                        Your machines
                    </p>
                    <h1 className="font-heading mt-1 text-5xl font-extrabold uppercase italic tracking-wide sm:text-6xl">
                        Garage
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Tap a bike to log fuel and track every kilometer
                    </p>
                </div>

                <Sheet open={sheetOpen} onOpenChange={handleSheetOpenChange}>
                    <SheetTrigger
                        render={
                            <Button className="bg-brand text-brand-foreground hover:bg-brand/90" />
                        }
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        Add bike
                    </SheetTrigger>
                    <SheetContent
                        side="right"
                        className="w-full overflow-y-auto border-white/10 sm:max-w-md"
                    >
                        <SheetHeader className="mb-6">
                            <SheetTitle>
                                {editingVehicle ? "Edit vehicle" : "Add new bike"}
                            </SheetTitle>
                        </SheetHeader>
                        <VehicleForm
                            defaultValues={editingVehicle ?? undefined}
                            onSubmit={handleSubmit}
                            isPending={createVehicle.isPending || updateVehicle.isPending}
                            error={createVehicle.error || updateVehicle.error}
                        />
                    </SheetContent>
                </Sheet>
            </div>

            {isLoading && (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {[1, 2].map((i) => (
                        <Skeleton key={i} className="h-44 rounded-2xl bg-white/5" />
                    ))}
                </div>
            )}

            {!isLoading && vehicles?.length === 0 && (
                <div className="surface-panel relative overflow-hidden px-6 py-16 text-center">
                    <p className="font-heading text-3xl font-bold uppercase italic tracking-wide">
                        Empty bay
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Roll in your first bike and start logging fuel
                    </p>
                </div>
            )}

            {!isLoading && vehicles && vehicles.length > 0 && (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {vehicles.map((vehicle, index) => (
                        <div
                            key={vehicle.id}
                            className="animate-fade-up"
                            style={{ animationDelay: `${index * 70}ms` }}
                        >
                            <VehicleCard
                                vehicle={vehicle}
                                onEdit={handleEdit}
                                onDelete={handleDelete}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
