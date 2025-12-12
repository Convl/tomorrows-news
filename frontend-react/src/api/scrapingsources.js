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
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.some((s) => s.currently_scraping)) {
        return 3000;
      }
      return 1000 * 300;
    },
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
      // Also invalidate the queries to trigger a re-fetch to be on the safe side
      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", data.topic_id],
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
      queryClient.setQueryData(["scrapingsource", data.id], (old) =>
        old ? { ...old, ...data } : data
      );
      queryClient.invalidateQueries({ queryKey: ["scrapingsource", data.id] });
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

export function useScrapeScrapingSourceNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sourceId, topicId }) => {
      return (
        await apiClient.post(`/scraping-sources/${sourceId}/trigger-scrape`)
      )?.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["scrapingsources", variables.topicId],
      });
      queryClient.invalidateQueries({
        queryKey: ["scrapingsource", variables.sourceId],
      });
    },
  });
}
