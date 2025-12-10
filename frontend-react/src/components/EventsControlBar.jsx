import {
  Paper,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Button,
  Box,
  FormControl,
  Select,
  MenuItem,
} from "@mui/material";

export default function EventsControlBar({
  sortBy,
  setSortBy,
  order,
  setOrder,
  allDescriptionsExpanded,
  allSourcesExpanded,
  handleToggleAllDescriptions,
  handleToggleAllSources,
}) {
  return (
    <Paper
      sx={{
        p: 2,
        mb: 2,
        display: "flex",
        alignItems: "center",
        gap: 2,
        flexWrap: "wrap",
      }}
    >
      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        Sort events by:
      </Typography>
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <Select
          value={sortBy}
          onChange={(event) => setSortBy(event.target.value)}
        >
          <MenuItem value="date">Date</MenuItem>
          <MenuItem value="relevance">Relevance</MenuItem>
        </Select>
      </FormControl>

      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        Order events by:
      </Typography>
      <ToggleButtonGroup
        value={order}
        exclusive
        onChange={(event, newOrder) => setOrder(newOrder)}
        size="small"
      >
        <ToggleButton value="ascending">Ascending</ToggleButton>
        <ToggleButton value="descending">Descending</ToggleButton>
      </ToggleButtonGroup>

      <Box sx={{ flexGrow: 1 }} />

      <Button
        size="small"
        variant="outlined"
        onClick={handleToggleAllDescriptions}
      >
        {allDescriptionsExpanded
          ? "Collapse all Descriptions"
          : "Expand all Descriptions"}
      </Button>

      <Button size="small" variant="outlined" onClick={handleToggleAllSources}>
        {allSourcesExpanded ? "Collapse all Sources" : "Expand all Sources"}
      </Button>
    </Paper>
  );
}
