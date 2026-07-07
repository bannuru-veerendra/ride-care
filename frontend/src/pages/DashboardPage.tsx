import useAuthStore from "@/store/auth.store";
import { Button } from "@/components/ui/button";

/**
 * Dashboard placeholder.
 * Will be fully implemented in a future iteration.
 */
export default function DashboardPage() {
  const clearToken = useAuthStore((state) => state.clearToken);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Welcome back</p>
        <Button variant="outline" onClick={clearToken}>Logout</Button>
      </div>
    </div>
  );
}
