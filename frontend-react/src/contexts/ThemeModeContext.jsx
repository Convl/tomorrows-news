import React from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { createAppTheme } from "../theme";

const ThemeModeContext = React.createContext({
  mode: "light",
  toggleMode: () => {},
});

export function ThemeModeProvider({ children }) {
  const [mode, setMode] = React.useState("light");

  const toggleMode = () =>
    setMode((prev) => (prev === "light" ? "dark" : "light"));
  const theme = React.useMemo(() => createAppTheme(mode), [mode]);

  return (
    <ThemeModeContext.Provider value={{ mode, toggleMode }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  );
}

export function useThemeMode() {
  return React.useContext(ThemeModeContext);
}
