import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  CircularProgress,
} from "@mui/material";

export default function DeleteConfirmationDialog({
  name,
  handleClose,
  handleDelete,
  isPending,
}) {
  return (
    <Dialog open={true} onClose={handleClose}>
      <DialogTitle>Delete Feed</DialogTitle>
      <DialogContent>
        <DialogContentText>
          ⚠️ Are you sure you want to delete "{name}"?
          <br />
          <br />
          This action cannot be undone. It will stop all scheduled scraping for
          this feed,{" "}
          <Box component="span" sx={{ fontWeight: "bold" }}>
            delete the feed and all events that have been extracted from it.
          </Box>
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={handleDelete}
          color="error"
          variant="contained"
          disabled={isPending}
          startIcon={isPending ? <CircularProgress size={20} /> : null}
        >
          {isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
