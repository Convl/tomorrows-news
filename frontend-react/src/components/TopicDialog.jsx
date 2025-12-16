import TopicForm from "./TopicForm";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Button,
  CircularProgress,
  Alert,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import React from "react";

export default function TopicDialog({ manager }) {
  const isEdit = !!manager.editingTopic;
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <Dialog
      open={true}
      onClose={manager.closeDialogs}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
    >
      <DialogTitle sx={{ fontSize: { xs: "1.1rem", sm: "1.25rem" } }}>
        {isEdit ? "📡 Edit Topic" : "📡 Create Topic"}
      </DialogTitle>
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
                flexDirection: { xs: "column", sm: "row" },
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
                  fullWidth={isMobile}
                  sx={{
                    fontSize: { xs: "0.875rem", sm: "0.875rem" },
                    order: { xs: 3, sm: 1 },
                  }}
                >
                  Delete Topic
                </Button>
              )}
              <Box
                sx={{
                  display: "flex",
                  gap: 2,
                  flexDirection: { xs: "column-reverse", sm: "row" },
                  width: { xs: "100%", sm: "auto" },
                  order: { xs: 1, sm: 2 },
                }}
              >
                <Button
                  variant="outlined"
                  onClick={manager.closeDialogs}
                  disabled={manager.isPending}
                  fullWidth={isMobile}
                  sx={{
                    fontSize: { xs: "0.875rem", sm: "0.875rem" },
                  }}
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
                  fullWidth={isMobile}
                  sx={{
                    fontSize: { xs: "0.875rem", sm: "0.875rem" },
                  }}
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
