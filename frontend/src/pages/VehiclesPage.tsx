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
 * Vehicles list page.
 * Shows all user vehicles with options to add, edit, and delete.
 * Add/edit uses a slide-in sheet panel (mobile-friendly).
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
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Vehicles</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Manage your registered vehicles
          </p>
        </div>

        <Sheet open={sheetOpen} onOpenChange={handleSheetOpenChange}>
          <SheetTrigger render={<Button size="sm" />}>
            <Plus className="h-4 w-4 mr-2" />
            Add vehicle
          </SheetTrigger>
          <SheetContent side="right" className="w-full sm:max-w-md overflow-y-auto">
            <SheetHeader className="mb-6">
              <SheetTitle>
                {editingVehicle ? "Edit vehicle" : "Add new vehicle"}
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

      {/* Loading state */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && vehicles?.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg font-medium">No vehicles yet</p>
          <p className="text-sm mt-1">
            Click "Add vehicle" to register your first vehicle
          </p>
        </div>
      )}

      {/* Vehicle grid */}
      {!isLoading && vehicles && vehicles.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {vehicles.map((vehicle) => (
            <VehicleCard
              key={vehicle.id}
              vehicle={vehicle}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
