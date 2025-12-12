import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  CircularProgress,
  Alert,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ScrapingSourceForm from "./ScrapingSourceForm";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import {
  useCreateScrapingSource,
  useUpdateScrapingSource,
  useDeleteScrapingSource,
} from "../api/scrapingsources";

// Helper function for formatting FastAPI errors
function formatFastAPIError(err) {
  if (err.response?.data?.detail) {
    const detail = err.response.data.detail;
    // return if single string (e.g. from raise HTTPException)
    if (typeof detail === "string") {
      return detail;
    }

    // Format each error as "field_name: error message" if possible
    if (Array.isArray(detail)) {
      return detail
        .map((error) => {
          const fieldName = Array.isArray(error.loc)
            ? error.loc.join(".")
            : null;
          const message = error?.msg || "Unknown error";
          return fieldName ? `${fieldName}: ${message}` : message;
        })
        .join("\n");
    }

    // Fallback
    return JSON.stringify(detail);
  }
  //Fallback
  else if (err?.message) {
    return err.message;
  }
  //Fallback
  else {
    return "Unknown error";
  }
}

// Dialog for creating/editing/deleting scraping sources. Rendered conditionally in the scraping sources tab of TopicDetail.
export default function ScrapingSourceDialog({
  onClose,
  topicId,
  sourceToEdit = null,
}) {
  // some conditional rendering logic differs depending on whether we are editing or creating a source
  const isEdit = !!sourceToEdit;

  // API mutations
  const createMutation = useCreateScrapingSource();
  const updateMutation = useUpdateScrapingSource();
  const deleteMutation = useDeleteScrapingSource();

  // Error state
  const [error, setError] = useState(null);

  // Delete confirmation dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Either create or update on submit
  const handleSubmit = async (data) => {
    try {
      setError(null);
      if (isEdit) {
        await updateMutation.mutateAsync({
          sourceId: sourceToEdit.id,
          data,
        });
      } else {
        await createMutation.mutateAsync({
          data,
          topicId,
        });
      }
      onClose();
    } catch (err) {
      const errorMessage = `Failed to ${
        isEdit ? "update" : "create"
      } source\n${formatFastAPIError(err)}`;
      setError(errorMessage);
    }
  };

  // Source deletion from delete confirmation dialog
  const handleDelete = async () => {
    try {
      setError(null);
      await deleteMutation.mutateAsync({
        sourceId: sourceToEdit.id,
        topicId: topicId,
      });
      setDeleteDialogOpen(false);
      onClose();
    } catch (err) {
      let errorMessage = "Failed to delete source";
      if (err.response?.data?.detail) {
        errorMessage = formatFastAPIError(err.response.data.detail);
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setDeleteDialogOpen(false);
    }
  };

  const isPending =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;

  return (
    <>
      <Dialog open={true} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>{isEdit ? "📡 Edit Feed" : "📡 Create Feed"}</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 3, whiteSpace: "pre-line" }}>
              {error}
            </Alert>
          )}
          <ScrapingSourceForm
            onSubmit={handleSubmit}
            defaultValues={
              isEdit
                ? sourceToEdit
                : {
                    degrees_of_separation: 1,
                    scraping_frequency: 1440,
                    is_active: true,
                  }
            }
            // passing submit / cancel / delete buttons to the form here as they depend on stuff like isEdit, DeleteDialog, etc
            formActions={
              <Box
                sx={{
                  mt: 3,
                  display: "flex",
                  gap: 2,
                  justifyContent: isEdit ? "space-between" : "flex-end",
                }}
              >
                {/* {TODO: Add option to delete / keep events that have been extracted from the feed} */}
                {isEdit && (
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => setDeleteDialogOpen(true)}
                    disabled={isPending}
                  >
                    Delete Feed
                  </Button>
                )}
                <Box sx={{ display: "flex", gap: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={onClose}
                    disabled={isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={isPending}
                    startIcon={
                      isPending ? <CircularProgress size={20} /> : null
                    }
                  >
                    {isPending
                      ? isEdit
                        ? "Saving..."
                        : "Creating..."
                      : isEdit
                      ? "Save Changes"
                      : "Create Feed"}
                  </Button>
                </Box>
              </Box>
            }
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      {deleteDialogOpen && (
        <DeleteConfirmationDialog
          name={sourceToEdit?.name}
          handleClose={() => setDeleteDialogOpen(false)}
          handleDelete={handleDelete}
          isPending={isPending}
        />
      )}
    </>
  );
}
