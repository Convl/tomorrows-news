import React from "react";
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
import ScrapingSourceForm from "./ScrapingSourceForm";

// Dialog for creating/editing/deleting scraping sources. Rendered conditionally in the scraping sources tab of TopicDetail.
export default function ScrapingSourceDialog({ manager }) {
  // some conditional rendering logic differs depending on whether we are editing or creating a source
  const isEdit = !!manager.editingSource;
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
        {isEdit ? "📡 Edit Feed" : "📡 Create Feed"}
      </DialogTitle>
      <DialogContent>
        {manager.error && (
          <Alert severity="error" sx={{ mb: 3, whiteSpace: "pre-line" }}>
            {manager.error}
          </Alert>
        )}
        <ScrapingSourceForm
          onSubmit={manager.handleSave}
          defaultValues={isEdit ? manager.editingSource : {}}
          // passing submit / cancel / delete buttons to the form here as they depend on stuff like isEdit, DeleteDialog, etc
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
              {/* {TODO: Add option to delete / keep events that have been extracted from the feed} */}
              {isEdit && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() =>
                    manager.openDeleteDialog(manager.editingSource)
                  }
                  disabled={manager.isPending}
                  fullWidth={isMobile}
                  sx={{
                    fontSize: { xs: "0.875rem", sm: "0.875rem" },
                    order: { xs: 3, sm: 1 },
                  }}
                >
                  Delete Feed
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
                    : "Create Feed"}
                </Button>
              </Box>
            </Box>
          }
        />
      </DialogContent>
    </Dialog>
  );
}
