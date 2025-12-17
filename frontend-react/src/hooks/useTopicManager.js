import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  useCreateTopic,
  useUpdateTopic,
  useDeleteTopic,
  useTopics,
} from "../api/topics";
import formatFastAPIError from "../utils/formatFastAPIError";

export function useTopicManager() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: topics } = useTopics();

  // State
  const [topicDialogOpen, setTopicDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [error, setError] = useState(null);

  // Sync dialog state with URL hash
  useEffect(() => {
    // If the hash is removed (e.g. back button), close the dialogs
    if (!location.hash) {
      setTopicDialogOpen(false);
      setDeleteDialogOpen(false);
      setEditingTopic(null);
      setError(null);
    }
  }, [location.hash]);

  // Mutations
  const createMutation = useCreateTopic();
  const updateMutation = useUpdateTopic();
  const deleteMutation = useDeleteTopic();

  const isPending =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;

  // Actions
  const openCreateDialog = () => {
    setEditingTopic(null);
    setError(null);
    setTopicDialogOpen(true);
    navigate("#create-topic");
  };

  const openEditDialog = (topic) => {
    setEditingTopic(topic);
    setError(null);
    setTopicDialogOpen(true);
    navigate("#edit-topic");
  };

  const openDeleteDialog = (topic) => {
    setEditingTopic(topic);
    setError(null);
    setDeleteDialogOpen(true);
    navigate("#delete-topic");
  };

  const closeDialogs = () => {
    setTopicDialogOpen(false);
    setDeleteDialogOpen(false);
    setEditingTopic(null);
    setError(null);
    if (location.hash) {
      navigate(-1);
    }
  };

  // Logic
  const handleSave = async (data) => {
    try {
      setError(null);
      if (editingTopic) {
        await updateMutation.mutateAsync({
          topicId: editingTopic.id,
          data,
        });
      } else {
        const newTopic = await createMutation.mutateAsync(data);
        // We need to navigate to the new topic, which clears the hash automatically
        navigate(`/dashboard/topics/${newTopic.id}`);
        // Return early since we navigated away
        closeDialogs();
        return;
      }
      closeDialogs();
    } catch (err) {
      const action = editingTopic ? "update" : "create";
      setError(`Failed to ${action} topic\n${formatFastAPIError(err)}`);
    }
  };

  const handleDelete = async () => {
    try {
      if (!editingTopic) return;
      const deletedId = editingTopic.id;
      await deleteMutation.mutateAsync({ topicId: deletedId });

      setDeleteDialogOpen(false);
      setEditingTopic(null);
      setError(null);

      if (topics) {
        const remaining = topics.filter((t) => t.id !== deletedId);
        if (remaining.length > 0) {
          navigate(`/dashboard/topics/${remaining[0].id}`);
        } else {
          navigate("/dashboard");
        }
      }
    } catch (err) {
      setError(`Failed to delete topic\n${formatFastAPIError(err)}`);
    }
  };

  return {
    // State
    topicDialogOpen,
    deleteDialogOpen,
    editingTopic,
    error,
    isPending,

    // Actions
    openCreateDialog,
    openEditDialog,
    openDeleteDialog,
    closeDialogs,
    handleSave,
    handleDelete,
  };
}
