import NavBar from "../components/NavBar";
import Button from "@mui/material/Button";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

export default function TestPage() {
  const { isPending, isError, data, error } = useQuery({
    queryKey: ["helloworld"],
    queryFn: () => apiClient.get("/debug/frontend").then((res) => res.data),
  });
  const res = isPending
    ? "Fetching data..."
    : isError
    ? `Encountered error: ${error.message}`
    : data.message;
  return (
    <>
      <NavBar />
      <h1>{res}</h1>
      <Button variant="contained">Test</Button>
    </>
  );
}
