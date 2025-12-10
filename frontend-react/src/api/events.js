import { useQuery } from "@tanstack/react-query";
import apiClient from "./client";

export function useEvents(topicId) {
  return useQuery({
    queryKey: ["events", topicId],
    queryFn: async () =>
      (await apiClient.get("/events", { params: { topic_id: topicId } }))?.data,
    refetchInterval: 30 * 1000,
  });
}
