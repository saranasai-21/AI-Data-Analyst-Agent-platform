class MemoryAgent:

    def initialize(self, state):

        if "conversation" not in state:
            state["conversation"] = []

        return state

    def save_user_message(
        self,
        state,
        query
    ):

        self.initialize(state)

        state["conversation"].append(
            {
                "role": "user",
                "content": query
            }
        )

        return state

    def save_assistant_message(
        self,
        state,
        response
    ):

        self.initialize(state)

        state["conversation"].append(
            {
                "role": "assistant",
                "content": response
            }
        )

        return state

    def get_context(
        self,
        state,
        max_turns=10
    ):

        self.initialize(state)

        return state[
            "conversation"
        ][-max_turns:]

    def clear_memory(
        self,
        state
    ):

        state["conversation"] = []

        return state