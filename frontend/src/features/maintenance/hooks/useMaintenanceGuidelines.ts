import { useQuery } from "@tanstack/react-query";
import {
  maintenanceGuidelinesApi,
  type Severity,
} from "@/api/maintenance-guidelines.api";

export const maintenanceKeys = {
  all: ["maintenance-guidelines"] as const,
  filtered: (severity?: Severity, component?: string) =>
    ["maintenance-guidelines", severity, component] as const,
  components: ["maintenance-guidelines-components"] as const,
  severityLevels: ["maintenance-guidelines-severity-levels"] as const,
};

export const useMaintenanceGuidelines = (
  severity?: Severity,
  component?: string
) => {
  return useQuery({
    queryKey: maintenanceKeys.filtered(severity, component),
    queryFn: () =>
      maintenanceGuidelinesApi.getAll({ severity, component }),
    staleTime: 1000 * 60 * 60 * 24, // 24 hours — data never changes
  });
};

export const useGuidelineComponents = () => {
  return useQuery({
    queryKey: maintenanceKeys.components,
    queryFn: maintenanceGuidelinesApi.getComponents,
    staleTime: 1000 * 60 * 60 * 24,
  });
};
