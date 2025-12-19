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

export function useCreateScrapingSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ data, topicId }) => {
      return (
        await apiClient.post("/scraping-sources/", {
          ...data,
          topic_id: topicId,
        })
      )?.data;
    },
    onSuccess: (data) => {
      // Update the cache with the new source
      queryClient.setQueryData(["scrapingsources", data.topic_id], (old) =>
        old ? [...old, data] : [data]
      );
      // We avoid invalidateQueries here to prevent overwriting optimistic states of other sources
      // (e.g. if one is currently scraping)
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
      queryClient.setQueryData(["scrapingsources", data.topic_id], (old) =>
        old
          ? old.map((source) => (source.id === data.id ? data : source))
          : [data]
      );
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
      const { data } = await apiClient.delete(`/scraping-sources/${sourceId}`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", data.topicId],
      });
    },
  });
}

export function useScrapeScrapingSourceNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sourceId, topicId }) => {
      return (
        await apiClient.post(`/scraping-sources/${sourceId}/trigger-scrape`)
      )?.data;
    },
  });
}
