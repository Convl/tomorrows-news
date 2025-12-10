import { Paper, Box, Typography, Chip, IconButton } from "@mui/material";
import PublicIcon from "@mui/icons-material/Public";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import ApiIcon from "@mui/icons-material/Api";
import LinkIcon from "@mui/icons-material/Link";
import EditIcon from "@mui/icons-material/Edit";

// individual scraping source card component
export default function ScrapingSourceCard({ source, onEdit }) {
  //Display time interval (since last scrape / until next scrape / overdue since) in two highest divisible units
  function formatTimeInterval(ms) {
    let result = "";
    let matched = 0;
    const units = {
      days: 86400000,
      hours: 3600000,
      minutes: 60000,
    };
    for (const [unit, value] of Object.entries(units)) {
      if (ms >= value && matched < 2) {
        matched += 1;
        const count = Math.floor(ms / value);
        result += `${count}${unit.charAt(0)} `;
        ms -= count * value;
      }
    }
    return result;
  }

  //Get status info for the source (due / overdue / never scraped / currently scraping)
  function getStatusInfo() {
    const now = new Date();
    const scrapingFrequencyMs = source.scraping_frequency * 60 * 1000;
    let lastScrapedDate = source.last_scraped_at
      ? new Date(source.last_scraped_at)
      : null;
    if (lastScrapedDate && lastScrapedDate.getFullYear() <= 1900) {
      lastScrapedDate = null;
    }

    const lastScrapedFormatted = lastScrapedDate
      ? formatTimeInterval(now - lastScrapedDate)
      : null;

    let statusDot = "";
    let statusText = "";
    let statusColor = "";

    if (source.currently_scraping) {
      statusDot = "🟡";
      statusText = `Currently scraping • Last scraped: ${
        lastScrapedFormatted ? `${lastScrapedFormatted} ago` : "never"
      }`;
      statusColor = "warning.main";
    } else if (lastScrapedDate) {
      const nextDueDate = new Date(
        lastScrapedDate.getTime() + scrapingFrequencyMs
      );
      const timeUntilNextDue = nextDueDate - now;
      const nextDueFormatted =
        timeUntilNextDue > 0
          ? `Due in ${formatTimeInterval(timeUntilNextDue)}`
          : `Overdue by ${formatTimeInterval(Math.abs(timeUntilNextDue))}`;

      if (timeUntilNextDue > 0) {
        statusDot = "🟢";
        statusText = `Last scraped: ${lastScrapedFormatted} ago • ${nextDueFormatted}`;
        statusColor = "success.main";
      } else {
        statusDot = "🔴";
        statusText = `Last scraped: ${lastScrapedFormatted} ago • ${nextDueFormatted}`;
        statusColor = "error.main";
      }
    } else {
      statusDot = "⚪";
      statusText = "Never scraped";
      statusColor = "text.disabled";
    }

    return { statusDot, statusText, statusColor };
  }

  const { statusDot, statusText, statusColor } = getStatusInfo();
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
  );
}
