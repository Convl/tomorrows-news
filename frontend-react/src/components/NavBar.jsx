import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import LightMode from "@mui/icons-material/LightMode";
import DarkMode from "@mui/icons-material/DarkMode";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import MenuIcon from "@mui/icons-material/Menu";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useThemeMode } from "../contexts/ThemeModeContext";

export default function NavBar({ onMenuClick }) {
  const { logout } = useAuth();
  const { mode, toggleMode } = useThemeMode();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
  }

  return (
    <AppBar position="static" elevation={1} color="primary" enableColorOnDark>
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 2, display: { lg: "none" } }}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Tomorrow's News
        </Typography>
        <Tooltip title="Help / Tutorial">
          <IconButton
            color="inherit"
            onClick={() => navigate("/dashboard/tutorial")}
            sx={{ mr: 1 }}
          >
            <HelpOutlineIcon />
          </IconButton>
        </Tooltip>
        <Tooltip
          title={`Switch to ${mode === "light" ? "dark" : "light"} mode`}
        >
          <IconButton color="inherit" onClick={toggleMode} sx={{ mr: 1 }}>
            {mode === "light" ? <DarkMode /> : <LightMode />}
          </IconButton>
        </Tooltip>
        <Button color="inherit" onClick={handleLogout}>
          Log out
        </Button>
      </Toolbar>
    </AppBar>
  );
}
