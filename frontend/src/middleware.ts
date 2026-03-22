import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/performance(.*)",
  "/pl(.*)",
  "/portfolio(.*)",
  "/sales-performance(.*)",
  "/departments(.*)",
  "/admin(.*)",
  "/reports(.*)",
  // Legacy redirects
  "/inter-month(.*)",
  "/month-end(.*)",
  "/executive(.*)",
  "/pace(.*)",
  "/sales(.*)",
]);

const devAuthBypass = process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";

export default clerkMiddleware(async (auth, req) => {
  if (devAuthBypass) return;
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
