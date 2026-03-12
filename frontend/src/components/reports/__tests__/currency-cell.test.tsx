import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CurrencyCell } from "../currency-cell";

function renderInTable(cell: React.ReactElement) {
  return render(
    <table>
      <tbody>
        <tr>{cell}</tr>
      </tbody>
    </table>
  );
}

describe("CurrencyCell", () => {
  it("renders formatted currency value", () => {
    renderInTable(<CurrencyCell value={100000} />);
    expect(screen.getByText("$1,000")).toBeInTheDocument();
  });

  it("renders dash for null value", () => {
    renderInTable(<CurrencyCell value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders zero value", () => {
    renderInTable(<CurrencyCell value={0} />);
    expect(screen.getByText("$0")).toBeInTheDocument();
  });

  it("renders negative value", () => {
    renderInTable(<CurrencyCell value={-50000} />);
    expect(screen.getByText("-$500")).toBeInTheDocument();
  });
});
