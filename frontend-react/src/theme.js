import { createTheme } from "@mui/material/styles";
import { teal } from "@mui/material/colors";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#2A9570",
    },
    secondary: {
      main: "#014991",
    },
    divider: "rgba(138,49,49,0.12)",
    error: {
      main: "#A50505",
    },
  },
});
