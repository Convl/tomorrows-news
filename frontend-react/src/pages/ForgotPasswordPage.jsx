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
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { FormContainer, TextFieldElement } from "react-hook-form-mui";
import apiClient from "../api/client";
import formatFastAPIError from "../utils/formatFastAPIError";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);

  const formContext = useForm({
    defaultValues: {
      email: "",
    },
  });

  const handleSubmit = async (data) => {
    try {
      setLoading(true);
      setError(null);

      await apiClient.post("/auth/forgot-password", {
        email: data.email,
      });

      setSuccess(true);
    } catch (err) {
      console.error(err);
      setError(formatFastAPIError(err));
    } finally {
      setLoading(false);
    }
  };

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
            Reset Email Sent
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            If an account exists for that email address, we have sent
            instructions for resetting your password.
          </Typography>
          <Button
            variant="contained"
            fullWidth
            onClick={() => navigate("/login")}
          >
            Return to Login
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
          Forgot Password
        </Typography>
        <Typography
          variant="body2"
          sx={{ mt: 1, mb: 2 }}
          color="text.secondary"
        >
          Enter your email address and we'll send you a link to reset your
          password.
        </Typography>
        <Box sx={{ mt: 1 }}>
          <FormContainer formContext={formContext} onSuccess={handleSubmit}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12 }}>
                <TextFieldElement
                  name="email"
                  label="Email Address"
                  required
                  fullWidth
                  autoComplete="email"
                  type="email"
                  autoFocus
                />
              </Grid>
            </Grid>
            <Typography
              sx={{ mt: 2 }}
              color={error ? "error.main" : "text.primary"}
            >
              {loading ? "Sending..." : error ?? ""}
            </Typography>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              Send Reset Link
            </Button>
            <Grid container justifyContent="flex-end">
              <Grid item>
                <Link component={RouterLink} to="/login" variant="body2">
                  Back to Sign in
                </Link>
              </Grid>
            </Grid>
          </FormContainer>
        </Box>
      </Paper>
    </Container>
  );
}
