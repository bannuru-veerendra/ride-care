import { useState } from "react";
import { Shield, Filter } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import GuidelineCard from "@/features/maintenance/components/GuidelineCard";
import {
  useMaintenanceGuidelines,
  useGuidelineComponents,
} from "@/features/maintenance/hooks/useMaintenanceGuidelines";
import { SEVERITY_CONFIG } from "@/features/maintenance/utils";
import type {
  MaintenanceGuideline,
  Severity,
} from "@/api/maintenance-guidelines.api";
import { cn } from "@/lib/utils";

const SEVERITY_LEVELS: Severity[] = ["critical", "high", "medium", "low"];

/**
 * Maintenance guidelines page.
 * Shows all guidelines grouped by component.
 * Filterable by severity and component.
 */
export default function MaintenanceGuidelinesPage() {
  const [selectedSeverity, setSelectedSeverity] = useState<
    Severity | undefined
  >(undefined);
  const [selectedComponent, setSelectedComponent] = useState<
    string | undefined
  >(undefined);
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);

  const { data: guidelines, isLoading } = useMaintenanceGuidelines(
    selectedSeverity,
    selectedComponent
  );
  const { data: components } = useGuidelineComponents();

  const grouped = guidelines?.reduce(
    (acc, guideline) => {
      const key = guideline.component;
      if (!acc[key]) acc[key] = [];
      acc[key].push(guideline);
      return acc;
    },
    {} as Record<string, MaintenanceGuideline[]>
  );

  const activeFilters =
    (selectedSeverity ? 1 : 0) + (selectedComponent ? 1 : 0);

  const clearFilters = () => {
    setSelectedSeverity(undefined);
    setSelectedComponent(undefined);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Maintenance</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Guidelines for keeping your ride in top condition
          </p>
        </div>

        <Sheet open={filterSheetOpen} onOpenChange={setFilterSheetOpen}>
          <SheetTrigger
            render={
              <Button
                variant="outline"
                size="sm"
                className="relative shrink-0"
              />
            }
          >
            <Filter className="mr-2 h-4 w-4" />
            Filter
            {activeFilters > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand text-[10px] font-bold text-brand-foreground">
                {activeFilters}
              </span>
            )}
          </SheetTrigger>
          <SheetContent
            side="right"
            className="w-full border-white/10 sm:max-w-sm"
          >
            <SheetHeader className="mb-6">
              <SheetTitle>Filter guidelines</SheetTitle>
            </SheetHeader>

            <div className="space-y-6 px-4 pb-4">
              <div className="space-y-3">
                <p className="text-sm font-medium">Severity</p>
                <div className="flex flex-wrap gap-2">
                  {SEVERITY_LEVELS.map((severity) => {
                    const config = SEVERITY_CONFIG[severity];
                    const active = selectedSeverity === severity;
                    return (
                      <Badge
                        key={severity}
                        className={cn(
                          "cursor-pointer select-none text-xs",
                          active
                            ? config.className
                            : "border-white/15 bg-transparent text-muted-foreground"
                        )}
                        onClick={() =>
                          setSelectedSeverity(active ? undefined : severity)
                        }
                      >
                        {config.label}
                      </Badge>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">Component</p>
                <div className="flex flex-wrap gap-2">
                  {components?.map((component) => {
                    const active = selectedComponent === component;
                    return (
                      <Badge
                        key={component}
                        variant={active ? "default" : "outline"}
                        className={cn(
                          "cursor-pointer select-none text-xs",
                          active
                            ? "border-0 bg-brand text-brand-foreground"
                            : "border-white/15 text-muted-foreground"
                        )}
                        onClick={() =>
                          setSelectedComponent(
                            active ? undefined : component
                          )
                        }
                      >
                        {component}
                      </Badge>
                    );
                  })}
                </div>
              </div>

              {activeFilters > 0 && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    clearFilters();
                    setFilterSheetOpen(false);
                  }}
                >
                  Clear all filters
                </Button>
              )}

              <Button
                className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
                onClick={() => setFilterSheetOpen(false)}
              >
                Apply
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {activeFilters > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">Filtered by:</span>
          {selectedSeverity && (
            <Badge
              className={cn(
                "cursor-pointer gap-1 text-xs",
                SEVERITY_CONFIG[selectedSeverity].className
              )}
              onClick={() => setSelectedSeverity(undefined)}
            >
              {SEVERITY_CONFIG[selectedSeverity].label} ×
            </Badge>
          )}
          {selectedComponent && (
            <Badge
              className="cursor-pointer gap-1 border-0 bg-brand/15 text-xs text-brand"
              onClick={() => setSelectedComponent(undefined)}
            >
              {selectedComponent} ×
            </Badge>
          )}
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      )}

      {!isLoading && guidelines?.length === 0 && (
        <div className="py-16 text-center text-muted-foreground">
          <Shield className="mx-auto mb-3 h-8 w-8 text-brand/40" />
          <p className="font-medium">No guidelines match your filters</p>
          <Button
            variant="link"
            className="mt-2 text-brand"
            onClick={clearFilters}
          >
            Clear filters
          </Button>
        </div>
      )}

      {!isLoading && grouped && Object.keys(grouped).length > 0 && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([component, items]) => (
            <section key={component}>
              <div className="mb-3 flex items-center gap-2">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">
                  {component}
                </p>
                <div className="h-px flex-1 bg-white/10" />
                <span className="text-xs text-muted-foreground">
                  {items.length} task{items.length === 1 ? "" : "s"}
                </span>
              </div>
              <div className="space-y-2">
                {items.map((guideline) => (
                  <GuidelineCard
                    key={guideline.id}
                    guideline={guideline}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
