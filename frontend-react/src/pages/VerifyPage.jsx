import React from "react";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import VerifiedUserIcon from "@mui/icons-material/VerifiedUser";
import GppBadIcon from "@mui/icons-material/GppBad";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import { useSearchParams, useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import formatFastAPIError from "../utils/formatFastAPIError";

export default function VerifyPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = React.useState("loading");
  const [errorMessage, setErrorMessage] = React.useState("");

  React.useEffect(() => {
    const verifyToken = async () => {
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setErrorMessage("No verification token provided.");
        return;
      }

      try {
        await apiClient.post("/auth/verify", { token });
        setStatus("success");
      } catch (error) {
        setStatus("error");
        setErrorMessage(
          formatFastAPIError(error) ||
            "The verification link is invalid or has expired."
        );
      }
    };

    verifyToken();
  }, [searchParams]);

  const renderContent = () => {
    if (status === "loading") {
      return (
        <>
          <CircularProgress sx={{ mb: 2 }} />
          <Typography component="h1" variant="h5" gutterBottom>
            Verifying Your Email
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Please wait while we verify your email address...
          </Typography>
        </>
      );
    } else if (status === "success") {
      return (
        <>
          <Avatar
            sx={{
              mx: "auto",
              bgcolor: "success.main",
              textAlign: "center",
              mb: 2,
              width: 56,
              height: 56,
            }}
          >
            <VerifiedUserIcon fontSize="large" />
          </Avatar>
          <Typography
            component="h1"
            variant="h5"
            gutterBottom
            color="success.main"
          >
            Email Verified!
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }} color="text.secondary">
            Your email has been successfully verified. You can now sign in to
            your account.
          </Typography>
          <Button
            variant="contained"
            fullWidth
            onClick={() => navigate("/login")}
          >
            Continue to Login
          </Button>
        </>
      );
    } else {
      return (
        <>
          <Avatar
            sx={{
              mx: "auto",
              bgcolor: "error.main",
              textAlign: "center",
              mb: 2,
              width: 56,
              height: 56,
            }}
          >
            <GppBadIcon fontSize="large" />
          </Avatar>
          <Typography
            component="h1"
            variant="h5"
            gutterBottom
            color="error.main"
          >
            Verification Failed
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }} color="text.secondary">
            {errorMessage}
          </Typography>
          <Box sx={{ display: "flex", gap: 2, flexDirection: "column" }}>
            <Button
              variant="contained"
              fullWidth
              onClick={() => navigate("/login")}
            >
              Return to Login
            </Button>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate("/signup")}
            >
              Create New Account
            </Button>
          </Box>
        </>
      );
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Paper
        elevation={8}
        sx={{
          marginTop: 8,
          padding: 4,
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {renderContent()}
      </Paper>
    </Container>
  );
}
