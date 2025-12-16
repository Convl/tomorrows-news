import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { fetchEventSource } from "@microsoft/fetch-event-source";

export default function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const controller = new AbortController();

    async function connectSSE() {
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
                const topicId = parseInt(parsedData.topic_id);

                // Update scraping sources cache
                queryClient.setQueryData(
                  ["scrapingsources", topicId],
                  (oldData) => {
                    if (!oldData) return oldData;
                    return oldData.map((source) =>
                      source.id === updatedSource.id
                        ? { ...source, ...updatedSource }
                        : source
                    );
                  }
                );
              } else if (parsedData.type === "event_update") {
                const updatedEvent = parsedData.payload;
                const topicId = parseInt(parsedData.topic_id);

                // Update events cache
                queryClient.setQueryData(["events", topicId], (oldData) => {
                  if (!oldData) return [updatedEvent];

                  const exists = oldData.some(
                    (event) => event.id === updatedEvent.id
                  );
                  if (exists) {
                    return oldData.map((event) =>
                      event.id === updatedEvent.id
                        ? { ...event, ...updatedEvent }
                        : event
                    );
                  } else {
                    // Add new event to the beginning of the list
                    return [updatedEvent, ...oldData];
                  }
                });
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
    }

    connectSSE();

    return () => {
      controller.abort();
    };
  }, [queryClient]);
}
