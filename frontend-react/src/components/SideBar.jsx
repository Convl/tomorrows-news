import React from "react";
import { NavLink, useParams } from "react-router-dom";
import { useTopics } from "../api/topics";
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  CircularProgress,
  Paper,
  Divider,
} from "@mui/material";
import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";
import AddIcon from "@mui/icons-material/Add";

export default function SideBar() {
  const { data: topics, isLoading } = useTopics();
  const { topicId } = useParams(); // useful if we want to do logic based on current selection

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Header Section */}
      <Box sx={{ p: 2, pb: 1 }}>
        <Typography
          variant="overline"
          sx={{
            fontWeight: "bold",
            color: "text.secondary",
            letterSpacing: 1.2,
          }}
        >
          TOPICS
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: "auto" }}>
        {isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <List sx={{ px: 1 }}>
            {topics?.map((topic) => (
              <ListItem key={topic.id} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  component={NavLink}
                  to={`/dashboard/topics/${topic.id}`}
                  sx={{
                    borderRadius: 1,
                    color: "text.secondary",
                    "&:hover": {
                      bgcolor: "action.hover",
                    },
                    "&.active": {
                      bgcolor: "primary.main",
                      color: "primary.contrastText",
                      "& .MuiListItemIcon-root": {
                        color: "inherit",
                      },
                      boxShadow: 1,
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <DocumentScannerIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={topic.name}
                    slotProps={{
                      primary: {
                        variant: "body2",
                        fontWeight: 500,
                      },
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <Divider />
      <Box sx={{ p: 2 }}>
        <ListItemButton
          sx={{
            borderRadius: 1,
            border: "1px dashed",
            borderColor: "text.disabled",
            justifyContent: "center",
            color: "text.secondary",
          }}
        >
          <AddIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="body2" fontWeight="bold">
            New Topic
          </Typography>
        </ListItemButton>
      </Box>
    </Box>
  );
}
