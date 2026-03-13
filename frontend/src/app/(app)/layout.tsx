import { PropertyProvider } from "@/providers/property-provider";
import { Sidebar } from "@/components/layout/sidebar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <PropertyProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="ml-[220px] min-h-screen flex-1 bg-gray-50 p-5">
          {children}
        </main>
      </div>
    </PropertyProvider>
  );
}
