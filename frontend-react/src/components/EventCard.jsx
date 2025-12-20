import { useTheme } from "@mui/material";
import {
  Card,
  CardContent,
  CardActions,
  Collapse,
  Typography,
  Box,
  Button,
  Stack,
  Chip,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LinkIcon from "@mui/icons-material/Link";
import Link from "@mui/material/Link";

export default function EventCard({
  event,
  descriptionExpanded,
  sourcesExpanded,
  onDescriptionExpandedChange,
  onSourcesExpandedChange,
}) {
  const theme = useTheme();
  const extractedEvents = event.extracted_events ?? [];
  // deduplicate extracted events by source URL, as multiple ExtractedEventDBs may be extracted from the same source URL,
  // but end up belonging to the same EventDB, cf the comment in consolidate_extracted_events in scraping_workflow.py
  const uniqueExtractedEvents = extractedEvents.reduce((acc, current) => {
    const x = acc.find((item) => item.source_url === current.source_url);
    if (!x) {
      acc.push(current);
    }
    return acc;
  }, []);

  const descriptionPreviewLength = 150;
  const shouldTruncate =
    event.description && event.description.length > descriptionPreviewLength;
  const descriptionPreview = shouldTruncate
    ? event.description.substring(0, descriptionPreviewLength) + "..."
    : event.description;

  function getSignificanceStyles(significance) {
    if (significance === null || significance === undefined) {
      return { bgcolor: "grey.400", color: theme.palette.common.white };
    }

    const shadowDepth = Math.round(significance * 9);
    const fontWeight = 400 + significance * 300;
    const fontColor =
      theme.palette.mode === "dark" || significance > 0.5
        ? theme.palette.primary.contrastText
        : theme.palette.primary.dark;

    const opacity = 0.1 + significance * 0.9;

    return {
      bgcolor: alpha(theme.palette.primary.main, opacity),
      color: fontColor,
      fontWeight: Math.round(fontWeight),
      border: `1px solid`,
      borderColor: theme.palette.primary.dark,
      boxShadow: shadowDepth > 0 ? shadowDepth : "none",
    };
  }

  const significance = event.significance ?? 0;
  const significancePercent = Math.round(significance * 100);
  const significanceStyles = getSignificanceStyles(significance);

  return (
    <Card
      sx={{
        mb: 2,
        position: "relative",
        boxShadow: 3,
        border: 1,
        borderColor: "divider",
        "&:hover": {
          bgcolor: "action.hover",
          boxShadow: theme.palette.mode === "light" ? 6 : 3,
        },
      }}
    >
      <CardContent sx={{ pb: 1.5, position: "relative" }}>
        <Chip
          label={`${significancePercent}%`}
          size="small"
          sx={{
            position: "absolute",
            top: 16,
            right: 16,
            ...significanceStyles,
          }}
        />
        <Typography variant="h6" component="div" gutterBottom sx={{ pr: 8 }}>
          {event.title}
        </Typography>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            mb: 1.5,
            color: "text.secondary",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <CalendarTodayIcon
              fontSize="small"
              sx={{ color: "primary.main" }}
            />
            <Typography variant="body2">
              {event.date
                ? new Date(event.date).toLocaleDateString()
                : "No known Date"}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <LocationOnIcon fontSize="small" sx={{ color: "primary.main" }} />
            <Typography variant="body2">
              {event.location || "No known Location"}
            </Typography>
          </Box>
        </Box>
        <Typography variant="body1">
          {descriptionExpanded ? event.description : descriptionPreview}
        </Typography>
      </CardContent>
      <CardActions>
        {shouldTruncate && (
          <Button
            size="small"
            onClick={() => onDescriptionExpandedChange(!descriptionExpanded)}
            endIcon={
              <ExpandMoreIcon
                sx={{
                  transform: descriptionExpanded
                    ? "rotate(180deg)"
                    : "rotate(0deg)",
                  transition: "transform 0.3s",
                }}
              />
            }
          >
            {descriptionExpanded
              ? "Collapse description"
              : "Expand description"}
          </Button>
        )}
        <Button
          size="small"
          onClick={() => onSourcesExpandedChange(!sourcesExpanded)}
          endIcon={
            <ExpandMoreIcon
              sx={{
                transform: sourcesExpanded ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.3s",
              }}
            />
          }
        >
          {sourcesExpanded ? "Collapse Sources" : "Expand Sources"}
        </Button>
      </CardActions>
      <Collapse in={sourcesExpanded} timeout={0} unmountOnExit>
        <CardContent
          sx={{
            bgcolor: alpha(theme.palette.primary.main, 0.05),
            borderTop: 1,
            borderColor: "divider",
          }}
        >
          <Typography variant="subtitle2" gutterBottom color="primary.main">
            SOURCES
          </Typography>
          {uniqueExtractedEvents.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No sources for this event.
            </Typography>
          ) : (
            <Stack spacing={1}>
              {uniqueExtractedEvents.map((source) => (
                <SourceCard key={source.id} source={source} />
              ))}
            </Stack>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
}

function SourceCard({ source }) {
  function extractDomain(url) {
    try {
      const { hostname } = new URL(url);
      const cleanHostname = hostname.replace(/^www\./, "");
      return cleanHostname.charAt(0).toUpperCase() + cleanHostname.slice(1);
    } catch {
      return url;
    }
  }

  function buildHighlightUrl(url, snippet) {
    if (!url) return "#";
    if (!snippet) return url;
    return `${url}#:~:text=${encodeURIComponent(snippet)}`;
  }

  const domain = extractDomain(source.source_url);
  const displayTitle = source.source_title
    ? `${domain}: ${source.source_title}`
    : `${domain}: Article`;
  const linkUrl = buildHighlightUrl(source.source_url, source.snippet);
  const published =
    source.source_published_date &&
    new Date(source.source_published_date).toLocaleString();

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1.5,
        p: 1.5,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        bgcolor: "background.paper",
      }}
    >
      <Box sx={{ color: "primary.main", pt: 0.3 }}>
        <LinkIcon fontSize="small" />
      </Box>
      <Box sx={{ flex: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}>
          <Link
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            underline="hover"
            sx={{ fontWeight: 600 }}
          >
            {displayTitle}
          </Link>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}>
          <CalendarTodayIcon fontSize="small" sx={{ color: "primary.main" }} />
          <Typography variant="body2" color="text.secondary">
            {published ? `Published ${published}` : "Publish date unknown"}
          </Typography>
        </Box>
        {source.snippet ? (
          <Box
            component="blockquote"
            sx={{
              m: 0,
              pl: 1.5,
              borderLeft: "3px solid",
              borderColor: "divider",
              color: "text.secondary",
              fontStyle: "italic",
            }}
          >
            “{source.snippet}”
          </Box>
        ) : null}
      </Box>
    </Box>
  );
}
