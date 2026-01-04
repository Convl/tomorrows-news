import React from "react";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import Grid from "@mui/material/Grid";
import Box from "@mui/material/Box";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { FormContainer, TextFieldElement } from "react-hook-form-mui";
import apiClient from "../api/client";
import formatFastAPIError from "../utils/formatFastAPIError";

export default function SignupPage() {
  const navigate = useNavigate();
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);

  const formContext = useForm({
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
    },
  });

  const handleSubmit = async (data) => {
    try {
      setLoading(true);
      setError(null);

      await apiClient.post("/auth/register", {
        email: data.email,
        password: data.password,
        first_name: data.firstName,
        last_name: data.lastName,
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
            <LockOutlinedIcon />
          </Avatar>
          <Typography component="h1" variant="h5" gutterBottom>
            Registration Successful
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Your account has been created. Please check your email to verify
            your account before logging in.
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
          <LockOutlinedIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          Sign up
        </Typography>
        <Box sx={{ mt: 3 }}>
          <FormContainer formContext={formContext} onSuccess={handleSubmit}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextFieldElement
                  name="firstName"
                  label="First Name"
                  required
                  fullWidth
                  autoFocus
                  autoComplete="given-name"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextFieldElement
                  name="lastName"
                  label="Last Name"
                  required
                  fullWidth
                  autoComplete="family-name"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextFieldElement
                  name="email"
                  label="Email Address"
                  required
                  fullWidth
                  autoComplete="email"
                  type="email"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextFieldElement
                  name="password"
                  label="Password"
                  required
                  fullWidth
                  type="password"
                  autoComplete="new-password"
                />
              </Grid>
            </Grid>
            <Typography
              sx={{ mt: 2 }}
              color={error ? "error.main" : "text.primary"}
            >
              {loading ? "Creating account..." : error ?? ""}
            </Typography>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              Sign Up
            </Button>
            <Grid container justifyContent="flex-end">
              <Grid item>
                <Link component={RouterLink} to="/login" variant="body2">
                  Already have an account? Sign in
                </Link>
              </Grid>
            </Grid>
          </FormContainer>
        </Box>
      </Paper>
    </Container>
  );
}
