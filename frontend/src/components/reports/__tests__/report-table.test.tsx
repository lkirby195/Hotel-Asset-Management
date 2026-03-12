import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReportTable } from "../report-table";
import type { ReportLineItem } from "@/lib/types";

// Mock the AccordionRow component since it has hook dependencies
vi.mock("../accordion-row", () => ({
  AccordionRow: ({ line }: { line: ReportLineItem }) => (
    <tr data-testid={`row-${line.code}`}>
      <td>{line.name}</td>
    </tr>
  ),
}));

const mockLines: ReportLineItem[] = [
  {
    id: "1",
    code: "room_revenue",
    name: "Room Revenue",
    parent_id: null,
    is_summary: true,
    data_type: "revenue",
    sort_order: 1,
    depth: 0,
    actual: 100000,
    budget: 80000,
    variance_dollars: 20000,
    variance_pct: 25.0,
    prior_year_actual: 90000,
    py_variance_dollars: 10000,
    py_variance_pct: 11.1,
  },
  {
    id: "2",
    code: "fb_total",
    name: "F&B Revenue",
    parent_id: null,
    is_summary: true,
    data_type: "revenue",
    sort_order: 2,
    depth: 0,
    actual: 50000,
    budget: 60000,
    variance_dollars: -10000,
    variance_pct: -16.7,
    prior_year_actual: null,
    py_variance_dollars: null,
    py_variance_pct: null,
  },
];

describe("ReportTable", () => {
  it("renders loading skeleton when isLoading", () => {
    render(<ReportTable lines={[]} period="mtd" isLoading={true} />);
    expect(screen.queryByText("Line Item")).not.toBeInTheDocument();
  });

  it("renders empty state when no lines", () => {
    render(<ReportTable lines={[]} period="mtd" isLoading={false} />);
    expect(screen.getByText("No data available for the selected period.")).toBeInTheDocument();
  });

  it("renders table headers", () => {
    render(<ReportTable lines={mockLines} period="mtd" isLoading={false} />);
    expect(screen.getByText("Line Item")).toBeInTheDocument();
    expect(screen.getByText("Actual")).toBeInTheDocument();
    expect(screen.getByText("Budget")).toBeInTheDocument();
    expect(screen.getByText("Variance")).toBeInTheDocument();
    expect(screen.getByText("Prior Year")).toBeInTheDocument();
    expect(screen.getByText("PY Variance")).toBeInTheDocument();
  });

  it("renders rows for each line item", () => {
    render(<ReportTable lines={mockLines} period="mtd" isLoading={false} />);
    expect(screen.getByTestId("row-room_revenue")).toBeInTheDocument();
    expect(screen.getByTestId("row-fb_total")).toBeInTheDocument();
  });
});
