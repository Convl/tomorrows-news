import TopicForm from "./TopicForm";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Button,
  CircularProgress,
  Alert,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import React from "react";

export default function TopicDialog({ manager }) {
  const isEdit = !!manager.editingTopic;

  return (
    <Dialog open={true} onClose={manager.closeDialogs} maxWidth="md" fullWidth>
      <DialogTitle>{isEdit ? "📡 Edit Topic" : "📡 Create Topic"}</DialogTitle>
      <DialogContent>
        {manager.error && (
          <Alert severity="error" sx={{ mb: 3, whiteSpace: "pre-line" }}>
            {manager.error}
          </Alert>
        )}
        <TopicForm
          defaultValues={isEdit ? manager.editingTopic : {}}
          handleSubmit={manager.handleSave}
          formActions={
            <Box
              sx={{
                mt: 3,
                display: "flex",
                gap: 2,
                justifyContent: isEdit ? "space-between" : "flex-end",
              }}
            >
              {isEdit && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => manager.openDeleteDialog(manager.editingTopic)}
                  disabled={manager.isPending}
                >
                  Delete Topic
                </Button>
              )}
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant="outlined"
                  onClick={manager.closeDialogs}
                  disabled={manager.isPending}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={manager.isPending}
                  startIcon={
                    manager.isPending ? <CircularProgress size={20} /> : null
                  }
                >
                  {manager.isPending
                    ? isEdit
                      ? "Saving..."
                      : "Creating..."
                    : isEdit
                    ? "Save Changes"
                    : "Create Topic"}
                </Button>
              </Box>
            </Box>
          }
        />
      </DialogContent>
    </Dialog>
  );
}
