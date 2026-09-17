import type { Document } from "@/features/documents/types";
import type { FuelLog } from "@/features/fuel-logs/types";
import type { ServiceLog } from "@/features/service-logs/types";

export type TimelineKind = "fuel" | "service" | "document";

export type TimelineEvent =
    | { kind: "fuel"; id: string; sortDate: string; payload: FuelLog }
    | { kind: "service"; id: string; sortDate: string; payload: ServiceLog }
    | { kind: "document"; id: string; sortDate: string; payload: Document };

const KIND_RANK: Record<TimelineKind, number> = {
    service: 0,
    fuel: 1,
    document: 2,
};

/** Normalize YYYY-MM-DD or ISO datetime to a calendar day for merge sort. */
export function timelineDay(value: string): string {
    return value.length >= 10 ? value.slice(0, 10) : value;
}

/**
 * Merge fuel, service, and document rows into one newest-first story.
 * Documents use vault `created_at`; logs use their event `date`.
 */
export function buildTimelineEvents(
    fuelLogs: FuelLog[],
    serviceLogs: ServiceLog[],
    documents: Document[]
): TimelineEvent[] {
    const events: TimelineEvent[] = [
        ...fuelLogs.map((payload) => ({
            kind: "fuel" as const,
            id: payload.id,
            sortDate: timelineDay(payload.date),
            payload,
        })),
        ...serviceLogs.map((payload) => ({
            kind: "service" as const,
            id: payload.id,
            sortDate: timelineDay(payload.date),
            payload,
        })),
        ...documents.map((payload) => ({
            kind: "document" as const,
            id: payload.id,
            sortDate: timelineDay(payload.created_at),
            payload,
        })),
    ];

    events.sort((a, b) => {
        if (a.sortDate !== b.sortDate) {
            return a.sortDate < b.sortDate ? 1 : -1;
        }
        const kindDiff = KIND_RANK[a.kind] - KIND_RANK[b.kind];
        if (kindDiff !== 0) return kindDiff;
        return a.id < b.id ? 1 : a.id > b.id ? -1 : 0;
    });

    return events;
}
