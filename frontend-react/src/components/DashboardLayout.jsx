import React from "react";
import { Outlet } from "react-router-dom";
import { Box, Toolbar } from "@mui/material";
import SideBar from "./SideBar";

export default function DashboardLayout() {
  return (
    <Box sx={{ display: "flex" }}>
      {/* 1. The Sidebar (Left) */}
      <SideBar />

      {/* 2. The Main Content (Right) */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* Toolbar spacer ensures content isn't hidden behind the fixed Navbar */}
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
