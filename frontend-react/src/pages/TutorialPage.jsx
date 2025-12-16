import React from "react";
import {
  List,
  ListItem,
  Typography,
  Paper,
  Container,
  ListItemText,
} from "@mui/material";

export default function TutorialPage() {
  return (
    <Container maxWidth="md">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome to Tomorrow's News
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          This Website allows you to track future events relating to your topics
          of interest from information found within user-specified online
          sources.
        </Typography>
        <Typography variant="h6" gutterBottom>
          Getting Started
        </Typography>
        <List>
          <ListItem>
            1. Create a Topic using the "New Topic" button in the sidebar. Be
            sure to add a detailed description of the topic and the kinds of
            events you are interested in as per the tooltip.
          </ListItem>
          <ListItem>
            2. Add sources under the "Information sources" tab of your topic.
            These can be e.g. news websites / rss feeds, events calendars, press
            portals, etc. Be sure to pay close attention to the tooltips.
          </ListItem>
          <ListItem>
            3. Events will become visible under the "Upcoming Events" tab of
            your topic as the information sources are being scraped.
          </ListItem>
        </List>
      </Paper>
    </Container>
  );
}
