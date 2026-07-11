import { Bike, Gauge, Calendar, Trash2, Pencil } from "lucide-react";
import { Link } from "react-router-dom";

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
 * Displays a single vehicle summary card.
 * Shows brand, name, year, registration, and odometer.
 * Provides edit and delete actions.
 */
export default function VehicleCard({ vehicle, onDelete, onEdit }: VehicleCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">
              <Link
                to={`/vehicles/${vehicle.id}`}
                className="hover:text-primary transition-colors"
              >
                {vehicle.brand} {vehicle.vehicle_name}
              </Link>
            </CardTitle>
            <Badge variant="secondary" className="mt-1 text-xs">
              {vehicle.registration_number}
            </Badge>
          </div>
          <div className="flex gap-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onEdit(vehicle)}
            >
              <Pencil className="h-3.5 w-3.5" />
              <span className="sr-only">Edit vehicle</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive hover:text-destructive"
              onClick={() => onDelete(vehicle.id)}
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
            <Calendar className="h-3.5 w-3.5 shrink-0" />
            <span>{vehicle.year}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Gauge className="h-3.5 w-3.5 shrink-0" />
            <span>{vehicle.current_odometer.toLocaleString("en-IN")} km</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground col-span-2">
            <Bike className="h-3.5 w-3.5 shrink-0" />
            <span>{vehicle.brand}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
