import React from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Button,
  CircularProgress,
  Chip,
  Link,
  Select,
  MenuItem,
  FormControl,
  ToggleButtonGroup,
  ToggleButton,
  Stack,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import AddIcon from "@mui/icons-material/Add";
import { useNavigate } from "react-router-dom";
import ArticleIcon from "@mui/icons-material/Article";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import LinkIcon from "@mui/icons-material/Link";
import WarningIcon from "@mui/icons-material/Warning";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useTopic } from "../api/topic";
import { useScrapingSources } from "../api/scrapingsources";
import { useEvents } from "../api/events";
import EventCard from "./EventCard";
import ScrapingSourceCard from "./ScrapingSourceCard";
import ScrapingSourceDialog from "./ScrapingSourceDialog";
import EventsControlBar from "./EventsControlBar";

export default function TopicDetail() {
  const { topicId } = useParams();
  const [tabValue, setTabValue] = React.useState(0);

  // Dialog state
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editingSource, setEditingSource] = React.useState(null);

  const handleAddClick = () => {
    setEditingSource(null);
    setDialogOpen(true);
  };

  const handleEditClick = (source) => {
    setEditingSource(source);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingSource(null);
  };

  const [sortBy, setSortBy] = React.useState("date");
  const [order, setOrder] = React.useState("ascending");
  const [allDescriptionsExpanded, setAllDescriptionsExpanded] =
    React.useState(false);
  const [allSourcesExpanded, setAllSourcesExpanded] = React.useState(false);
  const [expandedStates, setExpandedStates] = React.useState({});

  const { data: topic, isLoading: topicLoading } = useTopic(topicId);
  const { data: events, isLoading: eventsLoading } = useEvents(topicId);
  const { data: scrapingSources, isLoading: sourcesLoading } =
    useScrapingSources(topicId);

  const isLoading = topicLoading || eventsLoading || sourcesLoading;

  // Check scraping sources status
  const scrapingStatus = React.useMemo(() => {
    if (!scrapingSources || scrapingSources.length === 0) {
      return { hasOverdue: false, currentlyScraping: [], overdueSources: [] };
    }

    const now = new Date();
    const currentlyScraping = [];
    const overdueSources = [];

    scrapingSources.forEach((source) => {
      if (source.currently_scraping) {
        currentlyScraping.push(source);
      } else {
        const lastScrapedDate = source.last_scraped_at
          ? new Date(source.last_scraped_at)
          : null;
        if (lastScrapedDate && lastScrapedDate.getFullYear() > 1900) {
          const scrapingFrequencyMs =
            (source.scraping_frequency || 60) * 60 * 1000;
          const nextDueDate = new Date(
            lastScrapedDate.getTime() + scrapingFrequencyMs
          );
          if (nextDueDate < now) {
            overdueSources.push(source);
          }
        }
      }
    });

    return {
      currentlyScraping,
      overdueSources,
    };
  }, [scrapingSources]);

  const handleToggleAllDescriptions = () => {
    const newState = !allDescriptionsExpanded;
    setAllDescriptionsExpanded(newState);
    const newExpandedStates = { ...expandedStates };
    events?.forEach((event) => {
      newExpandedStates[`desc-${event.id}`] = newState;
    });
    setExpandedStates(newExpandedStates);
  };

  const handleToggleAllSources = () => {
    const newState = !allSourcesExpanded;
    setAllSourcesExpanded(newState);
    const newExpandedStates = { ...expandedStates };
    events?.forEach((event) => {
      newExpandedStates[`src-${event.id}`] = newState;
    });
    setExpandedStates(newExpandedStates);
  };

  const handleEventExpandedChange = (eventId, type, value) => {
    setExpandedStates((prev) => ({
      ...prev,
      [`${type}-${eventId}`]: value,
    }));
  };

  // Sort events
  const sortedEvents = React.useMemo(() => {
    if (!events || events.length === 0) return [];

    const sorted = [...events].sort((a, b) => {
      let comparison = 0;

      if (sortBy === "date") {
        const dateA = a.date ? new Date(a.date).getTime() : 0;
        const dateB = b.date ? new Date(b.date).getTime() : 0;
        comparison = dateA - dateB;
      } else if (sortBy === "relevance") {
        const sigA = a.significance ?? 0;
        const sigB = b.significance ?? 0;
        comparison = sigA - sigB;
      }

      return order === "ascending" ? comparison : -comparison;
    });

    return sorted;
  }, [events, sortBy, order]);

  if (isLoading) {
    return (
      <Box sx={{ p: 4, textAlign: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto" }}>
      {/* 1. Header Section */}
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            {topic?.name}
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            {topic?.keywords?.map((k) => (
              <Chip key={k} label={k} size="small" variant="outlined" />
            ))}
          </Box>
        </Box>
        <Button variant="outlined" startIcon={<EditIcon />}>
          Edit Topic
        </Button>
      </Box>
      {/* 2. Tabs Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(event, value) => setTabValue(value)}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab
            icon={<ArticleIcon />}
            iconPosition="start"
            label="Upcoming Events"
          />
          <Tab
            icon={<RssFeedIcon />}
            iconPosition="start"
            label={
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                }}
              >
                <Box>Scraping Feeds</Box>
                {scrapingStatus.overdueSources.length > 0 && (
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      mt: 0.25,
                    }}
                  >
                    <WarningIcon sx={{ fontSize: 12, color: "warning.main" }} />
                    <Typography
                      variant="caption"
                      sx={{ fontSize: "0.65rem", color: "warning.main" }}
                    >
                      Overdue for scraping:{" "}
                      {scrapingStatus.overdueSources
                        .map((s) => s.name)
                        .join(", ")}
                    </Typography>
                  </Box>
                )}
                {scrapingStatus.currentlyScraping.length > 0 && (
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      mt: scrapingStatus.hasOverdue ? 0.25 : 0.25,
                    }}
                  >
                    <CircularProgress
                      size={10}
                      sx={{ color: "warning.main" }}
                    />
                    <Typography
                      variant="caption"
                      sx={{ fontSize: "0.65rem", color: "warning.main" }}
                    >
                      Currently scraping:{" "}
                      {scrapingStatus.currentlyScraping
                        .map((s) => s.name)
                        .join(", ")}
                    </Typography>
                  </Box>
                )}
              </Box>
            }
          />
        </Tabs>
      </Paper>

      {/* 3. Tab Panels */}

      {/* PANEL 1: EVENTS */}
      <TabPanel value={tabValue} index={0}>
        {sortedEvents && sortedEvents.length > 0 ? (
          <>
            <EventsControlBar
              sortBy={sortBy}
              setSortBy={setSortBy}
              order={order}
              setOrder={setOrder}
              allDescriptionsExpanded={allDescriptionsExpanded}
              allSourcesExpanded={allSourcesExpanded}
              handleToggleAllDescriptions={handleToggleAllDescriptions}
              handleToggleAllSources={handleToggleAllSources}
            />

            {sortedEvents.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                descriptionExpanded={
                  expandedStates[`desc-${event.id}`] ?? false
                }
                sourcesExpanded={expandedStates[`src-${event.id}`] ?? false}
                onDescriptionExpandedChange={(value) =>
                  handleEventExpandedChange(event.id, "desc", value)
                }
                onSourcesExpandedChange={(value) =>
                  handleEventExpandedChange(event.id, "src", value)
                }
              />
            ))}
          </>
        ) : (
          <Paper
            sx={{
              p: 4,
              textAlign: "center",
              color: "text.secondary",
              bgcolor: "background.default",
            }}
          >
            <Typography>No events found for this topic.</Typography>
          </Paper>
        )}
      </TabPanel>

      {/* PANEL 2: SCRAPING SOURCES (FEEDS) */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
          <Button
            startIcon={<AddIcon />}
            variant="contained"
            size="small"
            onClick={handleAddClick}
          >
            Add New Feed
          </Button>
        </Box>

        {scrapingSources && scrapingSources.length > 0 ? (
          <Stack spacing={2}>
            {scrapingSources.map((source) => (
              <ScrapingSourceCard
                key={source.id}
                source={source}
                onEdit={handleEditClick}
              />
            ))}
          </Stack>
        ) : (
          <Paper
            sx={{
              p: 4,
              textAlign: "center",
              color: "text.secondary",
              bgcolor: "background.default",
            }}
          >
            <Typography>No scraping sources configured.</Typography>
          </Paper>
        )}

        {dialogOpen && (
          <ScrapingSourceDialog
            onClose={handleDialogClose}
            topicId={topicId}
            sourceToEdit={editingSource}
          />
        )}
      </TabPanel>
    </Box>
  );
}

// Wrapper Component for Tab Panels
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}
