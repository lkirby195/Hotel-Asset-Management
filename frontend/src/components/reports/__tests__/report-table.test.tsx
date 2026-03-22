import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReportTable } from "../ReportTable";
import type { ReportRow } from "@/types/reports";

// Mock the ReportRow component since it has hook dependencies
vi.mock("../ReportRow", () => ({
  ReportRow: ({ row }: { row: ReportRow }) => (
    <tr data-testid={`row-${row.line_item.code}`}>
      <td>{row.line_item.name}</td>
    </tr>
  ),
}));

const mockRows: ReportRow[] = [
  {
    line_item: {
      id: "1",
      code: "room_revenue",
      name: "Room Revenue",
      parent_id: null,
      department_type: null,
      sort_order: 1,
      is_summary: true,
      data_type: "revenue",
      has_children: true,
    },
    actual: 100000,
    budget: 80000,
    variance_dollar: 20000,
    variance_percent: 0.25,
    prior_year_actual: 90000,
    py_variance_dollar: 10000,
    py_variance_percent: 0.111,
  },
  {
    line_item: {
      id: "2",
      code: "fb_total",
      name: "F&B Revenue",
      parent_id: null,
      department_type: null,
      sort_order: 2,
      is_summary: true,
      data_type: "revenue",
      has_children: true,
    },
    actual: 50000,
    budget: 60000,
    variance_dollar: -10000,
    variance_percent: -0.167,
    prior_year_actual: 0,
    py_variance_dollar: 0,
    py_variance_percent: 0,
  },
];

const defaultProps = {
  rows: mockRows,
  expandedRows: new Set<string>(),
  childRowsMap: new Map<string, ReportRow[]>(),
  onToggleRow: vi.fn(),
  onChildrenLoaded: vi.fn(),
  showForecast: false,
  propertyId: "test-property",
  period: "mtd",
};

describe("ReportTable", () => {
  it("renders table headers with budget active by default", () => {
    render(<ReportTable {...defaultProps} />);
    expect(screen.getByText("Line item")).toBeInTheDocument();
    expect(screen.getByText("Actual")).toBeInTheDocument();
    expect(screen.getByText("Budget")).toBeInTheDocument();
    expect(screen.getByText("Bgt Var $")).toBeInTheDocument();
    expect(screen.getByText("Bgt Var %")).toBeInTheDocument();
  });

  it("renders rows for each line item", () => {
    render(<ReportTable {...defaultProps} />);
    expect(screen.getByTestId("row-room_revenue")).toBeInTheDocument();
    expect(screen.getByTestId("row-fb_total")).toBeInTheDocument();
  });

  it("shows STLY columns when stly comparison is active", () => {
    render(
      <ReportTable
        {...defaultProps}
        activeComparisons={new Set(["budget", "stly"])}
      />
    );
    expect(screen.getByText("STLY")).toBeInTheDocument();
    expect(screen.getByText("PY Var $")).toBeInTheDocument();
    expect(screen.getByText("PY Var %")).toBeInTheDocument();
  });

  it("shows forecast columns when forecast_lock comparison is active", () => {
    render(
      <ReportTable
        {...defaultProps}
        activeComparisons={new Set(["forecast_lock"])}
      />
    );
    expect(screen.getByText("Fcst Lock")).toBeInTheDocument();
    expect(screen.getByText("Fcst Var $")).toBeInTheDocument();
    expect(screen.getByText("Fcst Var %")).toBeInTheDocument();
  });
});
