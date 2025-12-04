import Avatar from "@mui/material/Avatar";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import React from "react";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);

      const formData = new URLSearchParams();
      formData.append("username", e.target.username.value);
      formData.append("password", e.target.password.value);

      const loginRes = await apiClient.post("/auth/jwt/login", formData);
      const loginData = loginRes.data;
      localStorage.setItem("token", loginData.access_token);

      const userRes = await apiClient.get("/users/me");
      const userData = userRes.data;
      login(userData);

      navigate("/");
    } catch (err) {
      localStorage.removeItem("token");
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 20 }}>
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
          <LockOutlinedIcon />{" "}
        </Avatar>
        <Typography
          component="h1"
          variant="h6"
          sx={{ textAlign: "center", mb: 2 }}
        >
          Log in to your account
        </Typography>
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            placeholder="Enter Email Address"
            fullWidth
            required
            autoFocus
            name="username"
            sx={{ mb: 1 }}
          ></TextField>
          <TextField
            placeholder="Enter password"
            fullWidth
            required
            name="password"
          ></TextField>
          <Typography sx={{ mt: 1 }} color={error ? "red" : "inherit"}>
            {loading ? "Logging in..." : error ?? ""}
          </Typography>
          <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }}>
            Sign in
          </Button>
          <Grid container justifyContent={"space-between"} sx={{ mt: 1 }}>
            <Grid>
              <Link
                component={RouterLink}
                to="/forgotpw"
                sx={{ color: "secondary.main" }}
              >
                Forgot password?
              </Link>
            </Grid>
            <Grid>
              <Link
                component={RouterLink}
                to="/signup"
                sx={{ color: "secondary.main" }}
              >
                Sign up
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Container>
  );
}
