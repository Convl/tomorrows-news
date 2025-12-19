import {
  Paper,
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
} from "@mui/material";
import PublicIcon from "@mui/icons-material/Public";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import ApiIcon from "@mui/icons-material/Api";
import LinkIcon from "@mui/icons-material/Link";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import UpdateIcon from "@mui/icons-material/Update";
import { useScrapeScrapingSourceNow } from "../api/scrapingsources";
import React from "react";
import { getScrapingSourceStatus } from "../utils/scrapingSourceStatus";

// individual scraping source card component
export default function ScrapingSourceCard({ source, onEdit, onDelete }) {
  const triggerScrape = useScrapeScrapingSourceNow();

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

          <Tooltip title="Trigger Scrape">
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
          </Tooltip>
          <Tooltip title="Delete Source">
            <IconButton
              size="small"
              color="primary"
              sx={{ alignSelf: "flex-start" }}
              onClick={() => onDelete(source)}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit Source">
            <IconButton
              size="small"
              color="primary"
              sx={{ alignSelf: "flex-start" }}
              onClick={() => onEdit(source)}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>
    </>
  );
}
