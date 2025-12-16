import { useState } from "react";
import {
  useCreateScrapingSource,
  useUpdateScrapingSource,
  useDeleteScrapingSource,
  useScrapeScrapingSourceNow,
} from "../api/scrapingsources";
import formatFastAPIError from "../utils/formatFastAPIError";

export function useScrapingSourceManager(topicId) {
  // State
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [error, setError] = useState(null);

  // Mutations
  const createMutation = useCreateScrapingSource();
  const updateMutation = useUpdateScrapingSource();
  const deleteMutation = useDeleteScrapingSource();
  const scrapeNowMutation = useScrapeScrapingSourceNow();

  const isPending =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    scrapeNowMutation.isPending;

  // Actions
  const openCreateDialog = () => {
    setEditingSource(null);
    setError(null);
    setSourceDialogOpen(true);
  };

  const openEditDialog = (source) => {
    setEditingSource(source);
    setError(null);
    setSourceDialogOpen(true);
  };

  const openDeleteDialog = (source) => {
    setEditingSource(source);
    setError(null);
    setDeleteDialogOpen(true);
  };

  const closeDialogs = () => {
    setSourceDialogOpen(false);
    setDeleteDialogOpen(false);
    setEditingSource(null);
    setError(null);
  };

  // Logic
  const handleSave = async (data) => {
    try {
      setError(null);
      if (editingSource) {
        await updateMutation.mutateAsync({
          sourceId: editingSource.id,
          data,
        });
      } else {
        await createMutation.mutateAsync({
          data,
          topicId,
        });
      }
      closeDialogs();
    } catch (err) {
      const action = editingSource ? "update" : "create";
      setError(`Failed to ${action} source\n${formatFastAPIError(err)}`);
    }
  };

  const handleDelete = async () => {
    try {
      if (!editingSource) return;
      await deleteMutation.mutateAsync({
        sourceId: editingSource.id,
        topicId,
      });
      closeDialogs();
    } catch (err) {
      setError(`Failed to delete source\n${formatFastAPIError(err)}`);
    }
  };

  const handleTriggerScrape = async (source) => {
    try {
      await scrapeNowMutation.mutateAsync({
        sourceId: source.id,
        topicId,
      });
    } catch (err) {
      setError(`Failed to trigger scrape\n${formatFastAPIError(err)}`);
    }
  };

  return {
    // State
    sourceDialogOpen,
    deleteDialogOpen,
    editingSource,
    error,
    isPending,

    // Actions
    openCreateDialog,
    openEditDialog,
    openDeleteDialog,
    closeDialogs,
    handleSave,
    handleDelete,
    handleTriggerScrape,
  };
}
