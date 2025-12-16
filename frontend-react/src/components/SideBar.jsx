import React, { useState } from "react";
import { NavLink, useParams } from "react-router-dom";
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
  IconButton,
  Menu,
  MenuItem,
} from "@mui/material";
import DocumentScannerIcon from "@mui/icons-material/DocumentScanner";
import AddIcon from "@mui/icons-material/Add";
import MoreHorizIcon from "@mui/icons-material/MoreHoriz";
import { alpha } from "@mui/material/styles";
import { useTheme } from "@mui/material/styles";

export default function SideBar({
  topics,
  isLoading,
  onAddTopic,
  onEditTopic,
  onDeleteTopic,
}) {
  const [anchorEl, setAnchorEl] = useState(null);
  const [menuTopic, setMenuTopic] = useState(null);
  const open = Boolean(anchorEl);

  const theme = useTheme();

  const handleMenuClick = (event, topic) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setMenuTopic(topic);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuTopic(null);
  };

  return (
    <Box
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        bgcolor: alpha(theme.palette.primary.main, 0.05),
      }}
    >
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
              <ListItem
                key={topic.id}
                disablePadding
                secondaryAction={
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuClick(e, topic)}
                    color="text.secondary"
                  >
                    <MoreHorizIcon fontSize="small" />
                  </IconButton>
                }
              >
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
            diabled: { isLoading },
          }}
          onClick={() => onAddTopic()}
        >
          <AddIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="body2" fontWeight="bold">
            New Topic
          </Typography>
        </ListItemButton>
      </Box>

      {/* Popup menu next to each topic */}
      <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
        <MenuItem
          onClick={() => {
            onEditTopic(menuTopic);
            handleMenuClose();
          }}
        >
          Edit topic
        </MenuItem>
        <MenuItem
          onClick={() => {
            onDeleteTopic(menuTopic);
            handleMenuClose();
          }}
        >
          Delete topic
        </MenuItem>
      </Menu>
    </Box>
  );
}
