import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import { useTopics } from "../api/topics";
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
} from "@mui/material";

export default function SideBar() {
  const { data: topics, isLoading } = useTopics();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 240,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: 240,
          boxSizing: "border-box",
        },
      }}
    >
      <Typography>Your topics</Typography>
      <Box sx={{ overflow: "auto" }}>
        <List>
          {topics && topics.map((topic) => <ListItem>{topic.name}</ListItem>)}
        </List>
      </Box>
    </Drawer>
  );
}
