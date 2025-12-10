import React from "react";
import { createRoutesFromElements, useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";

const AuthContext = React.createContext();

export function useAuth() {
  return React.useContext(AuthContext);
}

export default function AuthProvider({ children }) {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const navigate = useNavigate();

  React.useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setLoading(false);
      return;
    }

    apiClient
      .get("/users/me")
      .then((res) => {
        setUser(res.data);
        setLoading(false);
      })
      .catch((e) => {
        setLoading(false);
        navigate("/login");
      });
  }, [navigate]);

  const login = (loggedInUser) => setUser(loggedInUser);
  const logout = () => {
    setUser(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {loading && (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh",
          }}
        >
          <CircularProgress />
        </Box>
      )}
      {!loading && children}
    </AuthContext.Provider>
  );
}
