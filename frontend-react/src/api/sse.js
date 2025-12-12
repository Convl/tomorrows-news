import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { fetchEventSource } from "@microsoft/fetch-event-source";

export default function useSSE(topicId) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!topicId) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    const controller = new AbortController();

    async function connectSSE() {
      try {
        await fetchEventSource(
          `${import.meta.env.VITE_BACKEND_URL}${
            import.meta.env.VITE_API_BASE
          }/stream-sse`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: controller.signal,
            onmessage(event) {
              try {
                if (!event.data) return;

                const parsedData = JSON.parse(event.data);

                if (parsedData.type === "scraping_update") {
                  const updatedSource = parsedData.payload;

                  // Update scraping sources cache
                  queryClient.setQueryData(
                    ["scrapingsources", parseInt(topicId)],
                    (oldData) => {
                      if (!oldData) return oldData;
                      return oldData.map((source) =>
                        source.id === updatedSource.id
                          ? { ...source, ...updatedSource }
                          : source
                      );
                    }
                  );
                }
              } catch (err) {
                console.error("Error processing SSE message:", err);
              }
            },
            onerror(err) {
              // If unauthorized, stop retrying (user likely logged out or token expired)
              if (err.status === 401) {
                console.error("SSE Unauthorized, closing connection.");
                throw err; // Throwing error prevents retries
              }
            },
          }
        );
      } catch (err) {
        if (!controller.signal.aborted) {
          console.error("SSE Connection failed:", err);
        }
      }
    }

    connectSSE();

    return () => {
      controller.abort();
    };
  }, [topicId, queryClient]);
}
