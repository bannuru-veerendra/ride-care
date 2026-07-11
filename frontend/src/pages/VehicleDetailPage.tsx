import { useParams, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Gauge, Calendar, Fuel, Wrench, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { useVehicle } from "@/features/vehicles/hooks/useVehicles";

const tabTriggerClass =
    "font-heading flex-1 gap-2 rounded-none px-3 py-3.5 text-base font-bold uppercase tracking-wide text-muted-foreground after:!bottom-0 after:h-[2px] data-active:bg-transparent data-active:text-brand data-active:after:bg-brand data-active:after:opacity-100 sm:flex-none sm:px-5";

/**
 * Vehicle detail page.
 * Shows vehicle info and tabbed sections for fuel, service, and documents
 * (feature content added as each area is built).
 */
export default function VehicleDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: vehicle, isLoading: vehicleLoading } = useVehicle(id!);

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
            <div className="text-center py-16">
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
            <Link
                to="/vehicles"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
                <ArrowLeft className="h-4 w-4" />
                All vehicles
            </Link>

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
                        <span>
                            {vehicle.current_odometer.toLocaleString("en-IN")} km
                        </span>
                    </div>
                </div>
            </div>

            <Tabs defaultValue="fuel" className="gap-0">
                <TabsList
                    variant="line"
                    className="h-auto w-full justify-start gap-0 rounded-none border-b border-white/10 bg-transparent p-0"
                >
                    <TabsTrigger value="fuel" className={tabTriggerClass}>
                        <Fuel className="h-4 w-4" />
                        Fuel
                    </TabsTrigger>
                    <TabsTrigger value="service" className={tabTriggerClass}>
                        <Wrench className="h-4 w-4" />
                        Service
                    </TabsTrigger>
                    <TabsTrigger value="documents" className={tabTriggerClass}>
                        <FileText className="h-4 w-4" />
                        Docs
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="fuel" className="mt-4">
                    <div className="text-center py-12 text-muted-foreground">
                        <p className="font-medium">Fuel logs coming soon</p>
                    </div>
                </TabsContent>

                <TabsContent value="service" className="mt-4">
                    <div className="text-center py-12 text-muted-foreground">
                        <p className="font-medium">Service logs coming soon</p>
                    </div>
                </TabsContent>

                <TabsContent value="documents" className="mt-4">
                    <div className="text-center py-12 text-muted-foreground">
                        <p className="font-medium">Documents coming soon</p>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
