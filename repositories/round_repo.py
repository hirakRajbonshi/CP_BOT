class RoundRepo:
    """In-memory state management for pending and active rounds"""

    def __init__(self):
        self.pending_rounds = {}    # challenger_id -> Round
        self.accepted = {}          # challenger_id -> set of player_ids who accepted
        self.invited_to = {}        # opponent_id -> challenger_id (lookup for invitees)
        self.active_rounds = {}     # user_id -> Round

    # -------------------- Pending Rounds --------------------

    def add_pending_round(self, challenger_id, round_):
        """Store a new pending round and record all invitees."""
        self.pending_rounds[challenger_id] = round_
        # Challenger is pre-accepted
        self.accepted[challenger_id] = {challenger_id}
        # Map every opponent -> challenger so they can look up their invite
        for pid in round_.player_ids:
            if pid != challenger_id:
                self.invited_to[pid] = challenger_id

    def get_pending_round_for_invitee(self, opponent_id):
        """Return the pending round that this opponent was invited to, or None."""
        challenger_id = self.invited_to.get(opponent_id)
        if challenger_id is None:
            return None, None
        return challenger_id, self.pending_rounds.get(challenger_id)

    def accept(self, opponent_id):
        """Mark opponent as accepted. Returns (round, all_accepted: bool) or (None, False)."""
        challenger_id, round_ = self.get_pending_round_for_invitee(opponent_id)
        if not round_:
            return None, False

        self.accepted[challenger_id].add(opponent_id)
        all_accepted = self.accepted[challenger_id] == set(round_.player_ids)
        return round_, all_accepted

    def reject(self, opponent_id):
        """Opponent rejects — cancel the whole pending round. Returns the round or None."""
        challenger_id, round_ = self.get_pending_round_for_invitee(opponent_id)
        if not round_:
            return None
        self._cleanup_pending(challenger_id, round_)
        return round_

    def get_pending_round(self, challenger_id):
        """Return pending round for a challenger (for ;rcancel)."""
        return self.pending_rounds.get(challenger_id)

    def remove_pending_round(self, challenger_id):
        round_ = self.pending_rounds.get(challenger_id)
        if round_:
            self._cleanup_pending(challenger_id, round_)

    def _cleanup_pending(self, challenger_id, round_):
        self.pending_rounds.pop(challenger_id, None)
        self.accepted.pop(challenger_id, None)
        for pid in round_.player_ids:
            self.invited_to.pop(pid, None)

    # -------------------- Active Rounds --------------------

    def start_round(self, round_):
        """Finalise pending → active. Cleans up pending state first."""
        self._cleanup_pending(round_.challenger_id, round_)
        round_.start()
        for pid in round_.player_ids:
            self.active_rounds[pid] = round_

    def get_active_round(self, user_id):
        return self.active_rounds.get(user_id)

    def is_user_in_round(self, user_id):
        return (
            user_id in self.active_rounds
            or user_id in self.invited_to
            or user_id in self.pending_rounds
        )

    def remove_player_from_active(self, user_id):
        self.active_rounds.pop(user_id, None)

    def end_round(self, round_):
        for pid in list(round_.player_ids):
            self.active_rounds.pop(pid, None)
        # Clean up any stale references
        stale = [uid for uid, r in self.active_rounds.items() if r is round_]
        for uid in stale:
            self.active_rounds.pop(uid, None)
