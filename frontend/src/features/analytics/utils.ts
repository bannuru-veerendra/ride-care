/**
 * Chart prop types after mapping GET /vehicles/{id}/analytics series.
 * API points use date_label; charts plot the display label as `date`.
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
