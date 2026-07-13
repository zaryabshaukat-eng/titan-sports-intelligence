import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { AppShell } from "../components/titan/AppShell";
import { ThemeProvider } from "../components/titan/ThemeProvider";

function NotFoundComponent() {
  return (
    <AppShell>
      <div className="grid min-h-[60vh] place-items-center text-center">
        <div>
          <div className="font-display text-7xl font-bold text-gradient">404</div>
          <p className="mt-2 text-sm text-muted-foreground">This intelligence surface does not exist.</p>
        </div>
      </div>
    </AppShell>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <AppShell>
      <div className="grid min-h-[60vh] place-items-center text-center">
        <div className="max-w-md">
          <h1 className="font-display text-xl font-semibold">Signal disrupted</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            The Titan module encountered an unexpected fault. Reconnect below.
          </p>
          <button
            onClick={() => { router.invalidate(); reset(); }}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Reconnect
          </button>
        </div>
      </div>
    </AppShell>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Titan — Sports Intelligence OS" },
      { name: "description", content: "Enterprise-grade sports intelligence operating system combining market data, statistics, and explainable AI." },
      { name: "author", content: "Titan Intelligence" },
      { property: "og:title", content: "Titan — Sports Intelligence OS" },
      { property: "og:description", content: "The world's most advanced sports intelligence operating system." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AppShell>
          <Outlet />
        </AppShell>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
