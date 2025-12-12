import { Paper, Box, Typography, Chip, IconButton } from "@mui/material";
import PublicIcon from "@mui/icons-material/Public";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import ApiIcon from "@mui/icons-material/Api";
import LinkIcon from "@mui/icons-material/Link";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import ToggleOnIcon from "@mui/icons-material/ToggleOn";
import ToggleOffIcon from "@mui/icons-material/ToggleOff";
import UpdateIcon from "@mui/icons-material/Update";
import {
  useUpdateScrapingSource,
  useScrapeScrapingSourceNow,
} from "../api/scrapingsources";
import { useDeleteScrapingSource } from "../api/scrapingsources";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import React from "react";
import { getScrapingSourceStatus } from "../utils/scrapingSourceStatus";

// individual scraping source card component
export default function ScrapingSourceCard({ source, onEdit }) {
  const updateScrapingSource = useUpdateScrapingSource();
  const triggerScrape = useScrapeScrapingSourceNow();
  const deleteScrapingSource = useDeleteScrapingSource();
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);

  // Auto-update time display every minute
  const [_, setTick] = React.useState(0);
  React.useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 60000);
    return () => clearInterval(timer);
  }, []);

  const { statusDot, statusText, statusColor } =
    getScrapingSourceStatus(source);
  const sourceIcon =
    source.source_type === "Webpage" ? (
      <PublicIcon fontSize="small" />
    ) : source.source_type === "Rss" ? (
      <RssFeedIcon fontSize="small" />
    ) : source.source_type === "Api" ? (
      <ApiIcon fontSize="small" />
    ) : (
      <LinkIcon fontSize="small" />
    );

  return (
    <>
      <Paper
        sx={{
          p: 2,
          border: 1,
          borderColor: "divider",
          "&:hover": {
            bgcolor: "action.hover",
          },
        }}
      >
        <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
          <Box sx={{ color: "primary.main", pt: 0.5 }}>{sourceIcon}</Box>
          <Box sx={{ flex: 1 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                mb: 0.5,
                flexWrap: "wrap",
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {source.name}
              </Typography>
              <Chip
                label={source.source_type}
                size="small"
                variant="outlined"
                sx={{ height: 20, fontSize: "0.7rem" }}
              />
              <Typography
                variant="caption"
                sx={{ color: statusColor, fontSize: "0.75rem" }}
              >
                {statusDot} {statusText}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {source.base_url}
            </Typography>
          </Box>
          {/* <IconButton
            size="small"
            color={source.is_active ? "primary" : "grey"}
            sx={{ alignSelf: "flex-start" }}
            onClick={async () =>
              await updateScrapingSource.mutateAsync({
                sourceId: source.id,
                data: { is_active: !source.is_active },
              })
            }
          >
            {source.is_active ? (
              <ToggleOnIcon fontSize="small" />
            ) : (
              <ToggleOffIcon fontSize="small" />
            )}
          </IconButton> */}

          <IconButton
            size="small"
            color="primary"
            disabled={source.currently_scraping || triggerScrape.isPending}
            sx={{ alignSelf: "flex-start" }}
            onClick={async () =>
              await triggerScrape.mutateAsync({
                sourceId: source.id,
                topicId: source.topic_id,
              })
            }
          >
            <UpdateIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="primary"
            sx={{ alignSelf: "flex-start" }}
            onClick={() => setDeleteDialogOpen(true)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            color="primary"
            sx={{ alignSelf: "flex-start" }}
            onClick={() => onEdit(source)}
          >
            <EditIcon fontSize="small" />
          </IconButton>
        </Box>
      </Paper>
      {deleteDialogOpen && (
        <DeleteConfirmationDialog
          name={source.name}
          handleClose={() => setDeleteDialogOpen(false)}
          handleDelete={async () =>
            await deleteScrapingSource.mutateAsync({
              sourceId: source.id,
              topicId: source.topic_id,
            })
          }
          isPending={deleteScrapingSource.isPending}
        />
      )}
    </>
  );
}
