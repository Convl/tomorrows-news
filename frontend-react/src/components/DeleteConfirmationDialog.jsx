import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
} from "@mui/material";

export default function DeleteConfirmationDialog({ manager, warningText }) {
  return (
    <Dialog open={open} onClose={manager.closeDialogs}>
      <DialogTitle>Delete Feed</DialogTitle>
      <DialogContent>
        <DialogContentText>{warningText}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={manager.closeDialogs}>Cancel</Button>
        <Button
          onClick={manager.handleDelete}
          color="error"
          variant="contained"
          disabled={manager.isPending}
          startIcon={manager.isPending ? <CircularProgress size={20} /> : null}
        >
          {manager.isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
