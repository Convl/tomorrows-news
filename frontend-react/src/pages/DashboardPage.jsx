import React from "react";
import { Navigate } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";
import { useTopics } from "../api/topics";
import TutorialPage from "./TutorialPage";

export default function DashboardPage() {
  const { data: topics, isLoading } = useTopics();

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (topics && topics.length > 0) {
    return <Navigate to={`topics/${topics[0].id}`} replace />;
  }

  return <TutorialPage />;
}
