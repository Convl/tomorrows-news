// Helper function for formatting FastAPI errors
export default function formatFastAPIError(err) {
  if (err.response?.data?.detail) {
    const detail = err.response.data.detail;
    // return if single string (e.g. from raise HTTPException)
    if (typeof detail === "string") {
      return detail;
    }

    // Format each error as "field_name: error message" if possible
    if (Array.isArray(detail)) {
      return detail
        .map((error) => {
          const fieldName = Array.isArray(error.loc)
            ? error.loc.join(".")
            : null;
          const message = error?.msg || "Unknown error";
          return fieldName ? `${fieldName}: ${message}` : message;
        })
        .join("\n");
    }

    // Fallback
    return JSON.stringify(detail);
  }
  //Fallback
  else if (err?.message) {
    return err.message;
  }
  //Fallback
  else {
    return "Unknown error";
  }
}
