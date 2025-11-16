from game_state import GameState

print("--- NOMAD PROTOCOL ---")
agent = GameState()

agent.health -= 15
agent.creds += 500
agent.add_log_entry("Deal closed. [+500 CREDS]")
agent.add_log_entry("Ambush. [-15 HEALTH]")

print("Health:", agent.health, "/", agent.max_health)
print("Creds:", agent.creds)

print("\nLog:")
for entry in agent.log:
    print(entry)