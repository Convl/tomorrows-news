import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  useCreateTopic,
  useUpdateTopic,
  useDeleteTopic,
  useTopics,
} from "../api/topics";
import formatFastAPIError from "../utils/formatFastAPIError";

export function useTopicManager() {
  const navigate = useNavigate();
  const { data: topics } = useTopics();

  // State
  const [topicDialogOpen, setTopicDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [error, setError] = useState(null);

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
  };

  const openEditDialog = (topic) => {
    setEditingTopic(topic);
    setError(null);
    setTopicDialogOpen(true);
  };

  const openDeleteDialog = (topic) => {
    setEditingTopic(topic);
    setError(null);
    setDeleteDialogOpen(true);
  };

  const closeDialogs = () => {
    setTopicDialogOpen(false);
    setDeleteDialogOpen(false);
    setEditingTopic(null);
    setError(null);
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
        navigate(`/dashboard/topics/${newTopic.id}`);
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
      closeDialogs();

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
