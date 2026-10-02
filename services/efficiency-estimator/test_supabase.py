from supabase import create_client

# Hardcode credentials temporarily to test
url = "https://zoibotudsnkbrgmmywsd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvaWJvdHVkc25rYnJnbW15d3NkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MDg4MzI1NSwiZXhwIjoyMTA2NDU5MjU1fQ.hSUfKL5KaMQGJJH3OAolqtggUFkfHzJxJA1VUw33tlg"

supabase = create_client(url, key)

try:
    print("Attempting test insert...")
    response = supabase.table("batch_jobs").insert({
        "target_variable": "test_var",
        "total_iterations": 1,
        "summary_trend": [{"iteration": 0, "parameter_value": 0.5, "Efficiency_pct": 10.0, "Pmp": 1.0}]
    }).execute()
    print("SUCCESS! Response data:", response.data)
except Exception as e:
    print("FAILED with error:", e)