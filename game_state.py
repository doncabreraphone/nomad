class GameState:
    def __init__(self):
        self.health = 100
        self.max_health = 100
        self.creds = 50
        self.data = 0
        self.game_mode = 0
        self.log = []

    def add_log_entry(self, entry):
        self.log.append(entry)
        if len(self.log) > 20:
            self.log.pop(0)