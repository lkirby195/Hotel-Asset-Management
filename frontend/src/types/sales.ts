export type BookingStatus = 'definite' | 'tentative';

export interface SalespersonSummary {
  id: string;
  name: string;
  team: string;
  definite_revenue: number;
  tentative_revenue: number;
  definite_count: number;
  tentative_count: number;
  total_bookings: number;
}

export interface SalesBooking {
  id: string;
  salesperson_id: string;
  booking_date: string;
  status: BookingStatus;
  revenue: number;
  segment: string;
  event_name: string;
  event_date_start: string;
  event_date_end: string;
}

export interface SalesData {
  property_id: string;
  date_range: { start: string; end: string };
  salespeople: SalespersonSummary[];
}
