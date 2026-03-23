class DuelRepo:
    """In-memory state management for pending and active duels"""

    def __init__(self):
        self.pending_duels = {}   # opponent_id -> Duel
        self.active_duels = {}    # user_id -> Duel

    # -------------------- Pending Duels --------------------

    def add_pending_duel(self, opponent_id, duel):
        self.pending_duels[opponent_id] = duel

    def get_pending_duel(self, opponent_id):
        """Pop and return the pending duel for this opponent, or None"""
        return self.pending_duels.pop(opponent_id, None)

    def remove_pending_duel(self, opponent_id):
        self.pending_duels.pop(opponent_id, None)

    # -------------------- Active Duels --------------------

    def start_duel(self, duel):
        duel.start()
        self.active_duels[duel.challenger_id] = duel
        self.active_duels[duel.opponent_id] = duel

    def get_active_duel(self, user_id):
        return self.active_duels.get(user_id)

    def is_user_in_duel(self, user_id):
        return user_id in self.active_duels or user_id in self.pending_duels

    def end_duel(self, duel):
        self.active_duels.pop(duel.challenger_id, None)
        self.active_duels.pop(duel.opponent_id, None)
