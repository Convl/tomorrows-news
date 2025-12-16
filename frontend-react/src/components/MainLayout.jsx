import React from "react";
import { Outlet } from "react-router-dom";
import { Box, Drawer, useTheme, useMediaQuery, Alert } from "@mui/material";
import NavBar from "./NavBar";
import SideBar from "./SideBar";
import { useTopics } from "../api/topics";
import TopicDialog from "./TopicDialog";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import { useTopicManager } from "../hooks/useTopicManager";

const drawerWidth = 320;

export default function MainLayout() {
  const { data: topics, isLoading } = useTopics();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("lg"));

  const topicManager = useTopicManager();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleAddTopicClick = () => {
    topicManager.openCreateDialog();
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const sidebarContent = (
    <SideBar
      topics={topics}
      isLoading={isLoading}
      onAddTopic={handleAddTopicClick}
      onEditTopic={topicManager.openEditDialog}
      onDeleteTopic={topicManager.openDeleteDialog}
    />
  );

  return (
    <Box
      sx={{
        display: "grid",
        height: "100vh",
        gridTemplateAreas: isMobile
          ? `
          "header"
          "main"
        `
          : `
          "header header"
          "sidebar main"
        `,
        gridTemplateColumns: isMobile ? "1fr" : `${drawerWidth}px 1fr`,
        gridTemplateRows: "auto 1fr",
      }}
    >
      <Box sx={{ gridArea: "header", zIndex: 1100 }}>
        <NavBar onMenuClick={handleDrawerToggle} />
      </Box>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: "block", lg: "none" },
          "& .MuiDrawer-paper": {
            boxSizing: "border-box",
            width: drawerWidth,
          },
        }}
      >
        {sidebarContent}
      </Drawer>

      {/* Desktop Sidebar */}
      <Box
        component="aside"
        sx={{
          gridArea: "sidebar",
          display: { xs: "none", lg: "block" },
          borderRight: 1,
          borderColor: "divider",
          overflow: "auto",
          bgcolor: "background.paper",
        }}
      >
        {sidebarContent}
      </Box>

      <Box
        component="main"
        sx={{
          gridArea: "main",
          overflow: "auto",
          p: 3,
        }}
      >
        {topicManager.error &&
          !topicManager.topicDialogOpen &&
          !topicManager.deleteDialogOpen && (
            <Alert
              severity="error"
              onClose={topicManager.closeDialogs}
              sx={{ mb: 2, whiteSpace: "pre-line" }}
            >
              {topicManager.error}
            </Alert>
          )}
        <Outlet />
      </Box>

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
                delete the topic and all associated Feeds and Events.
              </Box>
            </>
          }
        />
      )}
    </Box>
  );
}
