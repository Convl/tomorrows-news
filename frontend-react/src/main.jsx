import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import App from "./App.jsx";
import { ThemeModeProvider } from "./contexts/ThemeModeContext.jsx";

// Debug Environment Variables
console.log("--- DEBUG ENV VARS ---");
console.log("VITE_BACKEND_URL raw:", import.meta.env.VITE_BACKEND_URL);
console.log("VITE_API_BASE raw:", import.meta.env.VITE_API_BASE);
console.log("----------------------");

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      gcTime: 5 * 60 * 1000,
      refetchOnMount: false,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: 2,
    },
  },
});

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools />
      <ThemeModeProvider>
        <App />
      </ThemeModeProvider>
    </QueryClientProvider>
  </StrictMode>
);
