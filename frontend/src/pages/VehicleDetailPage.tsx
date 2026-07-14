import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Plus, ArrowLeft, Gauge, Calendar, Hash, Fuel, Wrench, FileText } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { useVehicle } from "@/features/vehicles/hooks/useVehicles";
import FuelLogCard from "@/features/fuel-logs/components/FuelLogCard";
import FuelLogForm from "@/features/fuel-logs/components/FuelLogForm";
import {
    useFuelLogs,
    useCreateFuelLog,
    useUpdateFuelLog,
    useDeleteFuelLog,
} from "@/features/fuel-logs/hooks/useFuelLogs";
import type { FuelLog } from "@/features/fuel-logs/types";
import type { FuelLogSchema } from "@/features/fuel-logs/schemas";
import ServiceLogCard from "@/features/service-logs/components/ServiceLogCard";
import ServiceLogForm from "@/features/service-logs/components/ServiceLogForm";
import {
    useServiceLogs,
    useCreateServiceLog,
    useUpdateServiceLog,
    useDeleteServiceLog,
} from "@/features/service-logs/hooks/useServiceLogs";
import type { ServiceLog } from "@/features/service-logs/types";
import type { ServiceLogSchema } from "@/features/service-logs/schemas";

/**
 * Vehicle detail page.
 * Shows vehicle info and tabbed sections for fuel logs,
 * service logs, and documents (tabs added as features are built).
 */
export default function VehicleDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [fuelSheetOpen, setFuelSheetOpen] = useState(false);
    const [editingLog, setEditingLog] = useState<FuelLog | null>(null);

    const [serviceSheetOpen, setServiceSheetOpen] = useState(false);
    const [editingServiceLog, setEditingServiceLog] = useState<ServiceLog | null>(null);

    const { data: vehicle, isLoading: vehicleLoading } = useVehicle(id!);
    const { data: fuelLogs, isLoading: logsLoading } = useFuelLogs(id!);
    const { data: serviceLogs, isLoading: serviceLogsLoading } = useServiceLogs(id!);

    const createFuelLog = useCreateFuelLog(id!);
    const updateFuelLog = useUpdateFuelLog(id!, editingLog?.id ?? "");
    const deleteFuelLog = useDeleteFuelLog(id!);

    const createServiceLog = useCreateServiceLog(id!);
    const updateServiceLog = useUpdateServiceLog(id!, editingServiceLog?.id ?? "");
    const deleteServiceLog = useDeleteServiceLog(id!);

    const handleFuelSubmit = (values: FuelLogSchema) => {
        if (editingLog) {
            updateFuelLog.mutate(values, {
                onSuccess: () => {
                    toast.success("Fuel log updated");
                    setFuelSheetOpen(false);
                    setEditingLog(null);
                },
                onError: () => toast.error("Failed to update fuel log"),
            });
        } else {
            createFuelLog.mutate(values, {
                onSuccess: () => {
                    toast.success("Fuel log added");
                    setFuelSheetOpen(false);
                },
                onError: () => toast.error("Failed to add fuel log"),
            });
        }
    };

    const handleFuelEdit = (log: FuelLog) => {
        setEditingLog(log);
        setFuelSheetOpen(true);
    };

    const handleFuelDelete = (logId: string) => {
        if (!confirm("Delete this fuel log?")) return;
        deleteFuelLog.mutate(logId, {
            onSuccess: () => toast.success("Fuel log deleted"),
            onError: () => toast.error("Failed to delete fuel log"),
        });
    };

    const handleFuelSheetOpenChange = (open: boolean) => {
        setFuelSheetOpen(open);
        if (!open) setEditingLog(null);
    };

    const handleServiceSubmit = (values: ServiceLogSchema) => {
        const payload = {
            ...values,
            service_center: values.service_center || undefined,
            next_service_date: values.next_service_date || undefined,
            next_service_odometer: values.next_service_odometer || undefined,
            notes: values.notes || undefined,
        };

        if (editingServiceLog) {
            updateServiceLog.mutate(payload, {
                onSuccess: () => {
                    toast.success("Service log updated");
                    setServiceSheetOpen(false);
                    setEditingServiceLog(null);
                },
                onError: () => toast.error("Failed to update service log"),
            });
        } else {
            createServiceLog.mutate(payload, {
                onSuccess: () => {
                    toast.success("Service log added");
                    setServiceSheetOpen(false);
                },
                onError: () => toast.error("Failed to add service log"),
            });
        }
    };

    const handleServiceEdit = (log: ServiceLog) => {
        setEditingServiceLog(log);
        setServiceSheetOpen(true);
    };

    const handleServiceDelete = (logId: string) => {
        if (!confirm("Delete this service log?")) return;
        deleteServiceLog.mutate(logId, {
            onSuccess: () => toast.success("Service log deleted"),
            onError: () => toast.error("Failed to delete service log"),
        });
    };

    const handleServiceSheetOpenChange = (open: boolean) => {
        setServiceSheetOpen(open);
        if (!open) setEditingServiceLog(null);
    };

    if (vehicleLoading) {
        return (
            <div className="space-y-4">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-24 w-full rounded-xl" />
                <Skeleton className="h-64 w-full rounded-xl" />
            </div>
        );
    }

    if (!vehicle) {
        return (
            <div className="py-16 text-center">
                <p className="text-muted-foreground">Vehicle not found.</p>
                <Button
                    variant="link"
                    className="mt-2"
                    onClick={() => navigate("/vehicles")}
                >
                    Go back to vehicles
                </Button>
            </div>
        );
    }

    return (
        <div className="animate-fade-up space-y-8">
            {/* Back button */}
            <Link
                to="/vehicles"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
                <ArrowLeft className="h-4 w-4" />
                All vehicles
            </Link>

            {/* Vehicle header */}
            <div className="surface-panel relative overflow-hidden px-6 py-7 sm:px-8">
                <div
                    aria-hidden
                    className="absolute inset-y-0 left-0 w-1.5 bg-brand"
                />
                <div className="flex flex-wrap items-center gap-3">
                    <h1 className="font-heading text-4xl font-extrabold uppercase italic tracking-wide sm:text-5xl">
                        {vehicle.brand} {vehicle.vehicle_name}
                    </h1>
                    <Badge className="rounded-md border-0 bg-brand/15 font-semibold tracking-wide text-brand">
                        {vehicle.registration_number}
                    </Badge>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-brand" />
                        <span>{vehicle.year}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <Gauge className="h-3.5 w-3.5 text-brand" />
                        <span>{vehicle.current_odometer.toLocaleString("en-IN")} km</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <Hash className="h-3.5 w-3.5 text-brand" />
                        <span>{vehicle.registration_number}</span>
                    </div>
                </div>
            </div>

            {/* Tabs — one per feature */}
            <Tabs defaultValue="fuel" className="gap-0">
                <TabsList
                    variant="line"
                    className="h-auto w-full justify-start gap-0 rounded-none border-b border-white/10 bg-transparent p-0"
                >
                    <TabsTrigger
                        value="fuel"
                        className="font-heading flex-1 gap-2 rounded-none px-3 py-3.5 text-base font-bold uppercase tracking-wide text-muted-foreground after:!bottom-0 after:h-[2px] data-active:bg-transparent data-active:text-brand data-active:after:bg-brand data-active:after:opacity-100 sm:flex-none sm:px-5"
                    >
                        <Fuel className="h-4 w-4" />
                        Fuel
                    </TabsTrigger>
                    <TabsTrigger
                        value="service"
                        className="font-heading flex-1 gap-2 rounded-none px-3 py-3.5 text-base font-bold uppercase tracking-wide text-muted-foreground after:!bottom-0 after:h-[2px] data-active:bg-transparent data-active:text-brand data-active:after:bg-brand data-active:after:opacity-100 sm:flex-none sm:px-5"
                    >
                        <Wrench className="h-4 w-4" />
                        Service
                    </TabsTrigger>
                    <TabsTrigger
                        value="documents"
                        className="font-heading flex-1 gap-2 rounded-none px-3 py-3.5 text-base font-bold uppercase tracking-wide text-muted-foreground after:!bottom-0 after:h-[2px] data-active:bg-transparent data-active:text-brand data-active:after:bg-brand data-active:after:opacity-100 sm:flex-none sm:px-5"
                    >
                        <FileText className="h-4 w-4" />
                        Docs
                    </TabsTrigger>
                </TabsList>

                {/* Fuel logs tab */}
                <TabsContent value="fuel" className="mt-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            {fuelLogs?.length ?? 0} entries
                        </p>

                        <Sheet open={fuelSheetOpen} onOpenChange={handleFuelSheetOpenChange}>
                            <SheetTrigger
                                render={
                                    <Button
                                        size="sm"
                                        className="bg-brand text-brand-foreground hover:bg-brand/90"
                                    />
                                }
                            >
                                <Plus className="mr-2 h-4 w-4" />
                                Log fuel
                            </SheetTrigger>
                            <SheetContent
                                side="right"
                                className="w-full overflow-y-auto border-white/10 sm:max-w-md"
                            >
                                <SheetHeader className="mb-6">
                                    <SheetTitle className="font-heading text-2xl font-bold uppercase tracking-wide">
                                        {editingLog ? "Edit fuel log" : "Log fuel"}
                                    </SheetTitle>
                                    <p className="text-sm text-muted-foreground">
                                        Enter fill-up details — we calculate liters and km/l
                                    </p>
                                </SheetHeader>
                                <FuelLogForm
                                    defaultValues={editingLog ?? undefined}
                                    onSubmit={handleFuelSubmit}
                                    isPending={
                                        createFuelLog.isPending || updateFuelLog.isPending
                                    }
                                    error={createFuelLog.error || updateFuelLog.error}
                                />
                            </SheetContent>
                        </Sheet>
                    </div>

                    {logsLoading && (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <Skeleton key={i} className="h-24 rounded-xl" />
                            ))}
                        </div>
                    )}

                    {!logsLoading && fuelLogs?.length === 0 && (
                        <div className="surface-panel px-6 py-14 text-center">
                            <p className="font-heading text-2xl font-bold uppercase tracking-wide">
                                No fuel logs yet
                            </p>
                            <p className="mt-2 text-sm text-muted-foreground">
                                Tap "Log fuel" to record your first fill-up
                            </p>
                        </div>
                    )}

                    {!logsLoading && fuelLogs && fuelLogs.length > 0 && (
                        <div className="space-y-3">
                            {fuelLogs.map((log) => (
                                <FuelLogCard
                                    key={log.id}
                                    log={log}
                                    onDelete={handleFuelDelete}
                                    onEdit={handleFuelEdit}
                                />
                            ))}
                        </div>
                    )}
                </TabsContent>

                {/* Service logs tab */}
                <TabsContent value="service" className="mt-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            {serviceLogs?.length ?? 0} entries
                        </p>

                        <Sheet
                            open={serviceSheetOpen}
                            onOpenChange={handleServiceSheetOpenChange}
                        >
                            <SheetTrigger
                                render={
                                    <Button
                                        size="sm"
                                        className="bg-brand text-brand-foreground hover:bg-brand/90"
                                    />
                                }
                            >
                                <Plus className="mr-2 h-4 w-4" />
                                Log service
                            </SheetTrigger>
                            <SheetContent
                                side="right"
                                className="w-full overflow-y-auto border-white/10 sm:max-w-md"
                            >
                                <SheetHeader className="mb-6">
                                    <SheetTitle className="font-heading text-2xl font-bold uppercase tracking-wide">
                                        {editingServiceLog
                                            ? "Edit service log"
                                            : "Log service"}
                                    </SheetTitle>
                                    <p className="text-sm text-muted-foreground">
                                        Record what was done and when the next service is due
                                    </p>
                                </SheetHeader>
                                <ServiceLogForm
                                    key={editingServiceLog?.id ?? "create"}
                                    defaultValues={editingServiceLog ?? undefined}
                                    onSubmit={handleServiceSubmit}
                                    isPending={
                                        createServiceLog.isPending ||
                                        updateServiceLog.isPending
                                    }
                                    error={
                                        createServiceLog.error || updateServiceLog.error
                                    }
                                />
                            </SheetContent>
                        </Sheet>
                    </div>

                    {serviceLogsLoading && (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <Skeleton key={i} className="h-24 rounded-xl" />
                            ))}
                        </div>
                    )}

                    {!serviceLogsLoading && serviceLogs?.length === 0 && (
                        <div className="surface-panel px-6 py-14 text-center">
                            <p className="font-heading text-2xl font-bold uppercase tracking-wide">
                                No service logs yet
                            </p>
                            <p className="mt-2 text-sm text-muted-foreground">
                                Tap "Log service" to record your first service
                            </p>
                        </div>
                    )}

                    {!serviceLogsLoading && serviceLogs && serviceLogs.length > 0 && (
                        <div className="space-y-3">
                            {serviceLogs.map((log) => (
                                <ServiceLogCard
                                    key={log.id}
                                    log={log}
                                    onDelete={handleServiceDelete}
                                    onEdit={handleServiceEdit}
                                />
                            ))}
                        </div>
                    )}
                </TabsContent>

                {/* Documents tab — coming next */}
                <TabsContent value="documents" className="mt-4">
                    <div className="py-12 text-center text-muted-foreground">
                        <p className="font-medium">Documents coming soon</p>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
