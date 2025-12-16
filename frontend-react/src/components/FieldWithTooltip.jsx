import React from "react";
import { Box, Typography, Tooltip, IconButton } from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";

export default function FieldWithTooltip({ icon, label, children, tooltip }) {
  const styledIcon = React.cloneElement(icon, {
    fontSize: "small",
    color: icon.props.color || "primary",
    sx: { mr: 0.5, verticalAlign: "middle", ...icon.props.sx },
  });

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 0.5 }}>
        <Typography
          variant="body2"
          component="label"
          sx={{ display: "flex", alignItems: "center" }}
        >
          {styledIcon} {label}
        </Typography>
        <Tooltip title={tooltip} arrow>
          <IconButton size="small" sx={{ ml: 0.5, p: 0.5 }}>
            <InfoIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      {children}
    </Box>
  );
}
