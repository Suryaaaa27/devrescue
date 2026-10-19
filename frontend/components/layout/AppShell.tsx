import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#f7f7f5] text-zinc-950">
      <Sidebar />
      <Topbar />

      <main className="ml-64 pt-16">
        <div className="mx-auto max-w-[1600px] p-8">{children}</div>
      </main>
    </div>
  );
}