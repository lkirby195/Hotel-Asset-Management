export type PaceSegment = 'transient' | 'group' | 'contract';

export interface PaceCell {
  target_month: string;
  segment: PaceSegment;
  revenue_otb: number;
  rooms_otb: number;
  stly_revenue_otb: number;
  stly_rooms_otb: number;
  variance_stly_dollar: number;
  variance_stly_percent: number;
  pickup_7d: number;
  pickup_30d: number;
}

export interface PaceSubSegment {
  name: string;
  revenue_otb: number;
  rooms_otb: number;
}

export interface PaceData {
  property_id: string;
  property_name: string;
  as_of_date: string;
  segments: PaceSegment[];
  forward_months: string[];
  cells: PaceCell[];
  totals_by_month: {
    target_month: string;
    total_revenue_otb: number;
    total_stly_revenue: number;
  }[];
}

export interface PaceSegmentDetail {
  segment: PaceSegment;
  target_month: string;
  sub_segments: PaceSubSegment[];
}
