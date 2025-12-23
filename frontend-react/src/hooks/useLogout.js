import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../contexts/AuthContext";

export function useLogout() {
  const { logout } = useAuth();
  const queryClient = useQueryClient();

  return () => {
    queryClient.clear();
    logout();
  };
}
