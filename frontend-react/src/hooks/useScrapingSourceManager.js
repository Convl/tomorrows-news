import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  useCreateScrapingSource,
  useUpdateScrapingSource,
  useDeleteScrapingSource,
  useScrapeScrapingSourceNow,
} from "../api/scrapingsources";
import formatFastAPIError from "../utils/formatFastAPIError";

export function useScrapingSourceManager(topicId) {
  const navigate = useNavigate();
  const location = useLocation();

  // State
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [error, setError] = useState(null);

  // Sync dialog state with URL hash
  useEffect(() => {
    // If the hash is removed (e.g. back button), close the dialogs
    if (!location.hash) {
      setSourceDialogOpen(false);
      setDeleteDialogOpen(false);
      setEditingSource(null);
      setError(null);
    }
  }, [location.hash]);

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
    navigate("#create-feed");
  };

  const openEditDialog = (source) => {
    setEditingSource(source);
    setError(null);
    setSourceDialogOpen(true);
    navigate("#edit-feed");
  };

  const openDeleteDialog = (source) => {
    setEditingSource(source);
    setError(null);
    setDeleteDialogOpen(true);
    navigate("#delete-feed");
  };

  const closeDialogs = () => {
    setSourceDialogOpen(false);
    setDeleteDialogOpen(false);
    setEditingSource(null);
    setError(null);
    if (location.hash) {
      navigate(-1);
    }
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
