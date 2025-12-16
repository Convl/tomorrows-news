import { TextFieldElement, FormContainer } from "react-hook-form-mui";
import { Grid } from "@mui/material";
import BadgeIcon from "@mui/icons-material/Badge";
import InfoIcon from "@mui/icons-material/Info";
import FieldWithTooltip from "./FieldWithTooltip";

const tooltips = {
  name: "A succinct name for the topic about which upcoming events shall be gathered, e.g. 'Law & Legislation in Germany', 'International developments in artificial intelligence', 'Anything and everything having to do with UFOS'. The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard.",
  description:
    "A more detailed description of the topic and the kinds of events you are interested in, e.g.: 'Court cases and legislative proceedings in Germany that are significant enough to be of interest to the general public', 'Only focus on A.I. developments that are likely to impact the job market for software engineers within the next 12 months', 'I particularly care about UFO- and Alien-related Festivals and conventions'. The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard.",
  // is_active: "Whether the topic is active or not. The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard.",
};

export default function TopicForm({
  defaultValues,
  handleSubmit,
  formActions,
}) {
  const baseDefaults = {
    name: "",
    description: "",
  };
  const mergedDefaults = { ...baseDefaults, ...(defaultValues || {}) };

  return (
    <FormContainer
      defaultValues={mergedDefaults}
      onSuccess={async (data) => await handleSubmit(data)}
    >
      <Grid container spacing={3}>
        <Grid size={12}>
          <FieldWithTooltip
            icon={<BadgeIcon />}
            label="Name (required)"
            tooltip={tooltips.name}
          >
            <TextFieldElement
              name="name"
              fullWidth
              required
              placeholder="Enter topic name..."
            />
          </FieldWithTooltip>
        </Grid>
        <Grid size={12}>
          <FieldWithTooltip
            icon={<InfoIcon />}
            label="Description (required)"
            tooltip={tooltips.description}
          >
            <TextFieldElement
              name="description"
              fullWidth
              required
              multiline
              minRows={3}
              placeholder="Enter topic description..."
            />
          </FieldWithTooltip>
        </Grid>
      </Grid>
      {formActions}
    </FormContainer>
  );
}
