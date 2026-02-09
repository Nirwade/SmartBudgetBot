from SmartBudgetAI.chat_engine import handle_user_message
import time

print("🤖 Testing LLM Fallback (Slow Path)...")
start = time.time()

# This phrase has NO keywords (lend, gave, repaid) -> Regex will fail -> LLM must solve it
user_input = "Put 50 bucks on John's tab"

response = handle_user_message(user_input, user_id=99)
end = time.time()

print(f"\nUser: '{user_input}'")
print(f"Bot:  '{response}'")
print(f"⏱️ Time taken: {end - start:.2f}s")

if "lend" in response.lower() or "record" in response.lower():
    print("\n✅ SUCCESS: LLM understood the slang!")
else:
    print("\n❌ FAILURE: LLM did not trigger or failed to parse.")
