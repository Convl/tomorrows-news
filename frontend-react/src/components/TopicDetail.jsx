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
  Stack,
  Alert,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import AddIcon from "@mui/icons-material/Add";
import ArticleIcon from "@mui/icons-material/Article";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useTopic } from "../api/topic";
import { useTopics } from "../api/topics";
import { useScrapingSources } from "../api/scrapingsources";
import { useEvents } from "../api/events";
import useSSE from "../api/sse";
import EventCard from "./EventCard";
import ScrapingSourceCard from "./ScrapingSourceCard";
import ScrapingSourceDialog from "./ScrapingSourceDialog";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import EventsControlBar from "./EventsControlBar";
import { getScrapingSourceStatus } from "../utils/scrapingSourceStatus";
import TopicDialog from "./TopicDialog";
import { useTopicManager } from "../hooks/useTopicManager";
import { useScrapingSourceManager } from "../hooks/useScrapingSourceManager";
import DeleteIcon from "@mui/icons-material/Delete";
import { useAuth } from "../contexts/AuthContext";

export default function TopicDetail() {
  const { topicId: topicIdString } = useParams();
  const topicId = parseInt(topicIdString, 10);
  const [tabValue, setTabValue] = React.useState(0);
  const hasSetTab = React.useRef(false);

  // Reset tab selection state when topic changes
  React.useEffect(() => {
    hasSetTab.current = false;
    setDescriptionExpanded(false);
  }, [topicId]);

  // Managers
  const topicManager = useTopicManager();
  const sourceManager = useScrapingSourceManager(topicId);

  const [sortBy, setSortBy] = React.useState("date");
  const [order, setOrder] = React.useState("ascending");
  const [allDescriptionsExpanded, setAllDescriptionsExpanded] =
    React.useState(false);
  const [allSourcesExpanded, setAllSourcesExpanded] = React.useState(false);
  const [expandedStates, setExpandedStates] = React.useState({});

  const { data: topic, isLoading: topicLoading } = useTopic(topicId);
  const { data: events, isLoading: eventsLoading } = useEvents(topicId);
  const { data: scrapingSourcesData, isLoading: sourcesLoading } =
    useScrapingSources(topicId);
  const { user } = useAuth();

  // Logic to ensure topic description is collapsed (and expandable) if it spans > 2 lines on different devices
  const theme = useTheme();

  const isXl = useMediaQuery(theme.breakpoints.up("xl"));
  const isLg = useMediaQuery(theme.breakpoints.up("lg"));
  const isMd = useMediaQuery(theme.breakpoints.up("md"));
  const isSm = useMediaQuery(theme.breakpoints.up("sm"));

  const descriptionCharLimit =
    isXl || isLg ? 400 : isMd ? 300 : isSm ? 200 : 150;

  const topicDescriptionisExpandable =
    topic?.description &&
    (topic.description.length > descriptionCharLimit ||
      (topic.description.match(/\r\n|\r|\n/g) || []).length > 1);

  const [descriptionExpanded, setDescriptionExpanded] = React.useState(false);

  // Enable real-time updates
  useSSE();

  // Sort sources by creation date
  const scrapingSources = React.useMemo(() => {
    if (!scrapingSourcesData) return [];
    return [...scrapingSourcesData].sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at)
    );
  }, [scrapingSourcesData]);

  const isLoading = topicLoading || eventsLoading || sourcesLoading;

  // Auto-select tab based on sources availability
  // Only runs once per topic load when data becomes available
  React.useEffect(() => {
    if (!sourcesLoading && scrapingSourcesData && !hasSetTab.current) {
      if (scrapingSourcesData.length === 0) {
        setTabValue(1); // Open Sources tab if no sources
      } else {
        setTabValue(0); // Open Events tab if sources exist
      }
      hasSetTab.current = true;
    }
  }, [sourcesLoading, scrapingSourcesData, topicId]);

  // Get status info for all scraping sources with error states for quick view in the navigation tab
  const scrapingStatus = React.useMemo(() => {
    return scrapingSources.reduce(
      (acc, source) => {
        const status = getScrapingSourceStatus(source);
        if (["scraping", "failed", "overdue"].includes(status.state)) {
          acc[status.state].push({ source, status });
        }
        return acc;
      },
      {
        failed: [],
        scraping: [],
        overdue: [],
      }
    );
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
      {/* notification for demo users */}
      {user.is_demo_user && (
        <Alert
          severity="warning"
          sx={{
            borderRadius: 0,
            justifyContent: "center",
            py: 0.5,
            mb: 1,
            "& .MuiAlert-message": { width: "100%", textAlign: "center" },
          }}
        >
          You are logged in to a pre-configured demo account that is actively
          monitoring events for a number of topics. To create your own topics or
          perform other write operations, please log out first and set up your
          own account, as they will fail on this one.
        </Alert>
      )}
      {/* 1. Header Section */}
      <Box sx={{ mb: 4 }}>
        <Paper
          elevation={0}
          sx={{
            p: 3,
            bgcolor: "background.paper",
            border: 1,
            borderColor: "divider",
            borderRadius: 2,
          }}
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: { xs: "column", md: "row" },
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: 2,
              mb: 2,
            }}
          >
            <Typography variant="h4" fontWeight="bold">
              {topic?.name}
            </Typography>
            <Box
              sx={{
                display: "flex",
                gap: 1,
                width: { xs: "100%", md: "auto" },
                mt: { xs: 1, md: 0 },
              }}
            >
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={() => topicManager.openEditDialog(topic)}
                size="small"
                fullWidth={!isMd}
                sx={{ whiteSpace: "nowrap" }}
              >
                Edit
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => topicManager.openDeleteDialog(topic)}
                size="small"
                fullWidth={!isMd}
                sx={{ whiteSpace: "nowrap" }}
              >
                Delete
              </Button>
            </Box>
          </Box>

          {topic?.description && (
            <Box
              sx={{
                bgcolor: "action.hover",
                p: 2,
                borderRadius: 1,
                cursor: topicDescriptionisExpandable ? "pointer" : "default",
                transition: "background-color 0.2s",
                "&:hover": {
                  bgcolor: topicDescriptionisExpandable
                    ? "action.selected"
                    : "action.hover",
                },
              }}
              onClick={() =>
                topicDescriptionisExpandable &&
                setDescriptionExpanded(!descriptionExpanded)
              }
            >
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
                sx={{ fontSize: "0.75rem", textTransform: "uppercase" }}
              >
                Description
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  whiteSpace: "pre-line",
                  ...(!descriptionExpanded && {
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }),
                }}
              >
                {descriptionExpanded
                  ? topic.description
                  : topic.description.length > descriptionCharLimit
                  ? `${topic.description.slice(0, descriptionCharLimit)}...`
                  : topic.description}
              </Typography>
              {topicDescriptionisExpandable && (
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mt: 1,
                    color: "text.disabled",
                    "&:hover": { color: "primary.main" },
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                    {descriptionExpanded ? "SHOW LESS" : "SHOW MORE"}
                  </Typography>
                  {descriptionExpanded ? (
                    <ExpandLessIcon fontSize="small" />
                  ) : (
                    <ExpandMoreIcon fontSize="small" />
                  )}
                </Box>
              )}
            </Box>
          )}
        </Paper>
      </Box>

      {/* Global Errors from Managers */}
      {(topicManager.error || sourceManager.error) &&
        !topicManager.topicDialogOpen &&
        !topicManager.deleteDialogOpen &&
        !sourceManager.sourceDialogOpen &&
        !sourceManager.deleteDialogOpen && (
          <Alert
            severity="error"
            onClose={() => {
              topicManager.closeDialogs();
              sourceManager.closeDialogs();
            }}
            sx={{ mb: 2, whiteSpace: "pre-line" }}
          >
            {topicManager.error || sourceManager.error}
          </Alert>
        )}

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
                <Box>Information Sources</Box>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                    flexWrap: "wrap",
                  }}
                >
                  {/* Display summary of scraping sources with error states*/}
                  {["scraping", "failed", "overdue"]
                    .filter((state) => scrapingStatus[state].length > 0)
                    .map((state, index, arr) => {
                      const affectedSources = scrapingStatus[state];
                      return (
                        <React.Fragment key={state}>
                          <Typography
                            variant="caption"
                            sx={{
                              fontSize: "0.65rem",
                              color: affectedSources[0].status.statusColor,
                            }}
                          >
                            {state.charAt(0).toUpperCase() + state.slice(1)}:{" "}
                            {affectedSources.length}
                          </Typography>
                          {index < arr.length - 1 && (
                            <Typography
                              variant="caption"
                              sx={{
                                fontSize: "0.65rem",
                                color: "text.disabled",
                              }}
                            >
                              /
                            </Typography>
                          )}
                        </React.Fragment>
                      );
                    })}
                </Box>
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
            onClick={sourceManager.openCreateDialog}
          >
            Add New Source
          </Button>
        </Box>

        {scrapingSources && scrapingSources.length > 0 ? (
          <Stack spacing={2}>
            {scrapingSources.map((source) => (
              <ScrapingSourceCard
                key={source.id}
                source={source}
                onEdit={sourceManager.openEditDialog}
                onDelete={sourceManager.openDeleteDialog}
                onTriggerScrape={sourceManager.handleTriggerScrape}
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

        {sourceManager.sourceDialogOpen && (
          <ScrapingSourceDialog manager={sourceManager} />
        )}

        {sourceManager.deleteDialogOpen && (
          <DeleteConfirmationDialog
            manager={sourceManager}
            warningText={
              <>
                ⚠️ Are you sure you want to delete source "
                {`${sourceManager.editingSource?.name}`}"?
                <br />
                <br />
                This action cannot be undone.
              </>
            }
          />
        )}
      </TabPanel>

      {/* Dialogs - rendered outside TabPanel so they work from any tab */}
      {topicManager.topicDialogOpen && <TopicDialog manager={topicManager} />}

      {topicManager.deleteDialogOpen && (
        <DeleteConfirmationDialog
          manager={topicManager}
          warningText={
            <>
              ⚠️ Are you sure you want to delete "
              {`${topicManager.editingTopic?.name}`}"?
              <br />
              <br />
              This action cannot be undone. It will{" "}
              <Box component="span" sx={{ fontWeight: "bold" }}>
                delete the topic and all associated Sources and Events.
              </Box>
            </>
          }
        />
      )}
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
