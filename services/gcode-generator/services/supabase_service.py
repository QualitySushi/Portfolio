import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class SupabaseService:
    def __init__(self) -> None:
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")
        
        # Initialize client only if credentials exist, otherwise allow safe local fallback
        if url and key:
            self.client: Client | None = create_client(url, key)
        else:
            self.client = None

    def save_generation(self, user_id: str, file_type: str, output_data: str) -> None:
        """Saves generation results to the Supabase generations table."""
        if not self.client:
            print(f"[Supabase Mock] Client not configured. Skipped save for user {user_id} ({file_type}).")
            return

        try:
            self.client.table("generations").insert({
                "user_id": user_id,
                "file_type": file_type,
                "output_data": output_data,
            }).execute()
        except Exception as e:
            print(f"[Supabase Error] Failed to persist generation: {e}")

    # services/supabase_service.py (add this method if not already present)
    def get_user_generations(self, user_id: str) -> list:
        """Returns generation results for a user from the Supabase generations table."""
        if not self.client:
            print(
                f"[Supabase Mock] Client not configured. "
                f"Skipped fetch for user {user_id}."
            )
            return []

        try:
            response = (
                self.client
                .table("generations")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"[Supabase Error] Failed to fetch generations: {e}")
            return []


# Export a singleton instance to be imported across routers
supabase_service = SupabaseService()