import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PeriodToolbar } from "../period-toolbar";

describe("PeriodToolbar", () => {
  it("renders all period buttons", () => {
    render(<PeriodToolbar value="mtd" onChange={vi.fn()} />);
    expect(screen.getByText("MTD")).toBeInTheDocument();
    expect(screen.getByText("QTD")).toBeInTheDocument();
    expect(screen.getByText("YTD")).toBeInTheDocument();
    expect(screen.getByText("T28")).toBeInTheDocument();
    expect(screen.getByText("Weekly")).toBeInTheDocument();
    expect(screen.getByText("Custom")).toBeInTheDocument();
  });

  it("highlights the active period", () => {
    render(<PeriodToolbar value="qtd" onChange={vi.fn()} />);
    const qtdButton = screen.getByText("QTD");
    expect(qtdButton).toHaveClass("bg-gray-900");
  });

  it("calls onChange when a period is clicked", () => {
    const onChange = vi.fn();
    render(<PeriodToolbar value="mtd" onChange={onChange} />);

    fireEvent.click(screen.getByText("YTD"));
    expect(onChange).toHaveBeenCalledWith("ytd");
  });

  it("shows date picker when Custom is clicked", () => {
    render(<PeriodToolbar value="mtd" onChange={vi.fn()} />);

    fireEvent.click(screen.getByText("Custom"));
    expect(screen.getByText("Apply")).toBeInTheDocument();
  });

  it("does not show date picker initially", () => {
    render(<PeriodToolbar value="mtd" onChange={vi.fn()} />);
    expect(screen.queryByText("Apply")).not.toBeInTheDocument();
  });
});
