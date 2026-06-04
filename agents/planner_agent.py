class PlannerAgent:

    def __init__(self):

        self.visualization_keywords = [

            "chart",
            "plot",
            "graph",
            "visualize",
            "visualisation",
            "visualization",
            "heatmap",
            "histogram",
            "scatter",
            "line chart",
            "bar chart",
            "pie chart",
            "distribution",
            "trend",
            "dashboard"

        ]

    def run(self, query):

        query = query.lower()

        if any(
            keyword in query
            for keyword in self.visualization_keywords
        ):
            return "visualization"

        return "analysis"