import React from "react";
import { Outlet } from "react-router-dom";
import { Box } from "@mui/material";
import NavBar from "./NavBar";
import SideBar from "./SideBar";

export default function MainLayout() {
  return (
    <Box
      sx={{
        display: "grid",
        height: "100vh",
        gridTemplateAreas: `
          "header header"
          "sidebar main"
        `,
        gridTemplateColumns: "240px 1fr",
        gridTemplateRows: "auto 1fr",
      }}
    >
      <Box sx={{ gridArea: "header", zIndex: 1100 }}>
        <NavBar />
      </Box>

      <Box
        component="aside"
        sx={{
          gridArea: "sidebar",
          borderRight: 1,
          borderColor: "divider",
          overflow: "auto",
          bgcolor: "background.paper",
        }}
      >
        <SideBar />
      </Box>

      <Box
        component="main"
        sx={{
          gridArea: "main",
          overflow: "auto",
          p: 3,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
