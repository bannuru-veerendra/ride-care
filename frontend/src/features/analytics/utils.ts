/**
 * Chart prop types for analytics components.
 * Series data is produced by GET /vehicles/{id}/analytics.
 */

export interface MileageTrendPoint {
  date: string;
  mileage: number;
  odometer: number;
}

export interface MonthlySpendPoint {
  month: string;
  year_month?: string;
  spend: number;
  liters: number;
}
