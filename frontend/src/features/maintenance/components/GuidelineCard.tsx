import { useState } from "react";
import { ChevronDown, Clock, Gauge } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { MaintenanceGuideline } from "@/api/maintenance-guidelines.api";
import { SEVERITY_CONFIG } from "../utils";

interface GuidelineCardProps {
  guideline: MaintenanceGuideline;
}

/**
 * Expandable maintenance guideline card.
 * Shows task, interval, and severity badge.
 * Expands to show full description on tap.
 */
export default function GuidelineCard({ guideline }: GuidelineCardProps) {
  const [expanded, setExpanded] = useState(false);
  const severityConfig = SEVERITY_CONFIG[guideline.severity];

  return (
    <Card
      className="cursor-pointer border-white/10 bg-card/90 transition-colors hover:border-brand/40"
      onClick={() => setExpanded((prev) => !prev)}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium text-sm">{guideline.task}</p>
              <Badge className={cn("text-xs", severityConfig.className)}>
                {severityConfig.label}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
              {guideline.interval_km && (
                <div className="flex items-center gap-1.5">
                  <Gauge className="h-3.5 w-3.5 shrink-0 text-brand" />
                  <span>
                    Every {guideline.interval_km.toLocaleString("en-IN")} km
                  </span>
                </div>
              )}
              {guideline.interval_months && (
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 shrink-0 text-brand" />
                  <span>
                    Every {guideline.interval_months} month
                    {guideline.interval_months === 1 ? "" : "s"}
                  </span>
                </div>
              )}
              {!guideline.interval_km && !guideline.interval_months && (
                <span>As needed</span>
              )}
            </div>

            {expanded && (
              <p className="mt-2 border-t border-white/10 pt-1 text-sm leading-relaxed text-muted-foreground">
                {guideline.description}
              </p>
            )}
          </div>

          <ChevronDown
            className={cn(
              "mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-transform",
              expanded && "rotate-180"
            )}
          />
        </div>
      </CardContent>
    </Card>
  );
}
