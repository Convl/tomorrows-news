import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "./client";

export function useScrapingSources(topicId) {
  return useQuery({
    queryKey: ["scrapingsources", topicId],
    queryFn: async () =>
      (
        await apiClient.get("/scraping-sources", {
          params: { topic_id: topicId },
        })
      )?.data,
  });
}

export function useScrapingSource(sourceId) {
  return useQuery({
    queryKey: ["scrapingsource", sourceId],
    queryFn: async () =>
      (await apiClient.get(`/scraping-sources/${sourceId}`))?.data,
    enabled: !!sourceId,
  });
}

export function useCreateScrapingSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ data, topicId }) => {
      // API expects number, but we keep topicId as string for cache consistency
      const apiTopicId =
        typeof topicId === "string" ? parseInt(topicId, 10) : topicId;
      return (
        await apiClient.post("/scraping-sources/", {
          ...data,
          topic_id: apiTopicId,
        })
      )?.data;
    },
    onSuccess: (data, variables) => {
      // Use variables.topicId (string) to match useScrapingSources query key
      const topicId = variables.topicId;

      queryClient.setQueryData(["scrapingsources", topicId], (old) =>
        old ? [...old, data] : [data]
      );

      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", topicId],
      });
    },
  });
}

export function useUpdateScrapingSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sourceId, data }) => {
      return (await apiClient.put(`/scraping-sources/${sourceId}`, data))?.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["scrapingsource", data.id] });
      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", data.topic_id],
      });
    },
  });
}

export function useDeleteScrapingSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sourceId, topicId }) => {
      await apiClient.delete(`/scraping-sources/${sourceId}`);
      return { topicId };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", data.topicId],
      });
    },
  });
}
