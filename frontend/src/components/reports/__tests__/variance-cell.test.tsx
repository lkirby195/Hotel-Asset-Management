import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VarianceCell } from "../variance-cell";

function renderInTable(cell: React.ReactElement) {
  return render(
    <table>
      <tbody>
        <tr>{cell}</tr>
      </tbody>
    </table>
  );
}

describe("VarianceCell", () => {
  it("renders positive revenue variance as green", () => {
    renderInTable(
      <VarianceCell value={20000} percentage={25.0} dataType="revenue" />
    );
    const cell = screen.getByText("$200").closest("td");
    expect(cell).toHaveClass("text-green-700");
  });

  it("renders negative revenue variance as red", () => {
    renderInTable(
      <VarianceCell value={-10000} percentage={-12.5} dataType="revenue" />
    );
    const cell = screen.getByText("($100)").closest("td");
    expect(cell).toHaveClass("text-red-700");
  });

  it("renders negative expense variance as green (favorable)", () => {
    renderInTable(
      <VarianceCell value={-5000} percentage={-10.0} dataType="expense" />
    );
    const cell = screen.getByText("($50)").closest("td");
    expect(cell).toHaveClass("text-green-700");
  });

  it("renders positive expense variance as red (unfavorable)", () => {
    renderInTable(
      <VarianceCell value={5000} percentage={10.0} dataType="expense" />
    );
    const cell = screen.getByText("$50").closest("td");
    expect(cell).toHaveClass("text-red-700");
  });

  it("renders percentage when provided", () => {
    renderInTable(
      <VarianceCell value={20000} percentage={25.0} dataType="revenue" />
    );
    expect(screen.getByText("+25.0%")).toBeInTheDocument();
  });

  it("hides percentage when null", () => {
    renderInTable(
      <VarianceCell value={20000} percentage={null} dataType="revenue" />
    );
    expect(screen.queryByText("%")).not.toBeInTheDocument();
  });

  it("zero revenue variance is green", () => {
    renderInTable(
      <VarianceCell value={0} percentage={0} dataType="revenue" />
    );
    const cell = screen.getByText("$0").closest("td");
    expect(cell).toHaveClass("text-green-700");
  });

  it("zero expense variance is green", () => {
    renderInTable(
      <VarianceCell value={0} percentage={0} dataType="expense" />
    );
    const cell = screen.getByText("$0").closest("td");
    expect(cell).toHaveClass("text-green-700");
  });
});
