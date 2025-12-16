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
    onMutate: async ({ sourceId, topicId }) => {
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({
        queryKey: ["scrapingsources", topicId],
      });

      // backup previous sources
      const previousSources = queryClient.getQueryData([
        "scrapingsources",
        topicId,
      ]);
      // optimistically update the cache (TODO: consider switching to broadcasting start of scraping in backend)
      queryClient.setQueryData(["scrapingsources", topicId], (old) =>
        old
          ? old.map((source) =>
              source.id === sourceId
                ? { ...source, currently_scraping: true }
                : source
            )
          : [{ id: sourceId, currently_scraping: true }]
      );
      return { previousSources };
    },
    onError: (error, variables, context) => {
      // revert to previous sources on error
      queryClient.setQueryData(
        ["scrapingsources", topicId],
        context.previousSources
      );
    },
  });
}
