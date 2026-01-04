import React from "react";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import KeyIcon from "@mui/icons-material/Key";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { FormContainer, TextFieldElement } from "react-hook-form-mui";
import apiClient from "../api/client";
import formatFastAPIError from "../utils/formatFastAPIError";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);

  const formContext = useForm({
    defaultValues: {
      password: "",
      passwordConfirm: "",
    },
  });

  const handleSubmit = async (data) => {
    if (data.password !== data.passwordConfirm) {
      setError("Passwords do not match");
      return;
    }

    if (!token) {
        setError("Missing reset token");
        return;
    }

    try {
      setLoading(true);
      setError(null);

      await apiClient.post("/auth/reset-password", {
        token: token,
        password: data.password,
      });

      setSuccess(true);
    } catch (err) {
      console.error(err);
      setError(formatFastAPIError(err));
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
     return (
        <Container maxWidth="sm" sx={{ mt: 10 }}>
            <Paper elevation={8} sx={{ marginTop: 8, padding: 4, textAlign: "center" }}>
                <Typography color="error">Invalid or missing reset token.</Typography>
                <Button component={RouterLink} to="/login" sx={{ mt: 2 }}>Back to Login</Button>
            </Paper>
        </Container>
     )
  }

  if (success) {
    return (
      <Container maxWidth="sm" sx={{ mt: 10 }}>
        <Paper
          elevation={8}
          sx={{ marginTop: 8, padding: 4, textAlign: "center" }}
        >
          <Avatar
            sx={{
              mx: "auto",
              bgcolor: "success.main",
              textAlign: "center",
              mb: 2,
            }}
          >
            <KeyIcon />
          </Avatar>
          <Typography component="h1" variant="h5" gutterBottom>
            Password Reset Successful
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Your password has been successfully reset. You can now log in with your new password.
          </Typography>
          <Button
            variant="contained"
            fullWidth
            onClick={() => navigate("/login")}
          >
            Go to Login
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 10 }}>
      <Paper
        elevation={8}
        sx={{ marginTop: 8, padding: 2, textAlign: "center" }}
      >
        <Avatar
          sx={{
            mx: "auto",
            bgcolor: "primary.main",
            textAlign: "center",
            mb: 1,
          }}
        >
          <KeyIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          Reset Password
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, mb: 2 }} color="text.secondary">
            Enter your new password below.
        </Typography>
        <Box sx={{ mt: 1 }}>
          <FormContainer formContext={formContext} onSuccess={handleSubmit}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12 }}>
                <TextFieldElement
                  name="password"
                  label="New Password"
                  required
                  fullWidth
                  type="password"
                  autoFocus
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextFieldElement
                  name="passwordConfirm"
                  label="Confirm Password"
                  required
                  fullWidth
                  type="password"
                />
              </Grid>
            </Grid>
            <Typography
              sx={{ mt: 2 }}
              color={error ? "error.main" : "text.primary"}
            >
              {loading ? "Resetting..." : error ?? ""}
            </Typography>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              Set New Password
            </Button>
          </FormContainer>
        </Box>
      </Paper>
    </Container>
  );
}

