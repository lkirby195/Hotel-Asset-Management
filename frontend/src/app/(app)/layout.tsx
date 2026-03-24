import { PropertyProvider } from "@/providers/property-provider";
import { TopNav } from "@/components/layout/top-nav";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <PropertyProvider>
      <div className="min-h-screen bg-surface-50">
        <TopNav />
        <main>{children}</main>
      </div>
    </PropertyProvider>
  );
}
