import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "./client";

export function useTopic(topicId) {
  return useQuery({
    queryKey: ["topic", topicId],
    queryFn: async () => (await apiClient.get(`/topics/${topicId}`))?.data,
    staleTime: 5 * 60 * 1000,
  });
}
