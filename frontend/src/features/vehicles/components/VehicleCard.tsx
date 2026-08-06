import { Gauge, Calendar, Trash2, Pencil, ChevronRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Vehicle } from "../types";

interface VehicleCardProps {
    vehicle: Vehicle;
    onDelete: (id: string) => void;
    onEdit: (vehicle: Vehicle) => void;
}

/**
 * Vehicle garage card — click to open vehicle details.
 */
export default function VehicleCard({ vehicle, onDelete, onEdit }: VehicleCardProps) {
    const navigate = useNavigate();

    return (
        <Card
            className="group relative cursor-pointer overflow-hidden border-white/10 bg-card/90 transition-all duration-300 hover:-translate-y-1 hover:border-brand/50"
            onClick={() => navigate(`/vehicles/${vehicle.id}`)}
        >
            <div
                aria-hidden
                className="absolute inset-y-0 left-0 w-1 bg-brand opacity-70 transition-all group-hover:opacity-100 group-hover:w-1.5"
            />

            <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                        <CardTitle className="font-heading text-2xl font-bold uppercase italic tracking-wide">
                            <Link
                                to={`/vehicles/${vehicle.id}`}
                                className="transition-colors group-hover:text-brand"
                                onClick={(e) => e.stopPropagation()}
                            >
                                {vehicle.brand} {vehicle.vehicle_name}
                            </Link>
                        </CardTitle>
                        <Badge className="mt-2 rounded-md border-0 bg-brand/15 text-xs font-semibold tracking-wide text-brand">
                            {vehicle.registration_number}
                        </Badge>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit(vehicle);
                            }}
                        >
                            <Pencil className="h-3.5 w-3.5" />
                            <span className="sr-only">Edit vehicle</span>
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete(vehicle.id);
                            }}
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                            <span className="sr-only">Delete vehicle</span>
                        </Button>
                    </div>
                </div>
            </CardHeader>

            <CardContent>
                <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5 shrink-0 text-brand" />
                        <span>{vehicle.year}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Gauge className="h-3.5 w-3.5 shrink-0 text-brand" />
                        <span>{vehicle.current_odometer.toLocaleString("en-IN")} km</span>
                    </div>
                    <div className="col-span-2 flex justify-end">
                        <span className="inline-flex items-center gap-0.5 text-xs font-bold uppercase tracking-wider text-brand opacity-0 transition-opacity group-hover:opacity-100">
                            Ride log
                            <ChevronRight className="h-3.5 w-3.5" />
                        </span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
