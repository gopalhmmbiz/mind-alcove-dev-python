from langgraph.graph import START, END, StateGraph


from app.services.activity_suggestion.state import RecommendationState
# Define the graph & import all nodes
from app.services.activity_suggestion.process_inputs import process_inputs
from app.services.activity_suggestion.select_activities import get_activity_suggestions


builder = StateGraph(RecommendationState)

# Add nodes
builder.add_node('process_inputs', process_inputs)
builder.add_node('select_activities', get_activity_suggestions)

# Add edges
builder.add_edge(START, 'process_inputs')
builder.add_edge('process_inputs', 'select_activities')
builder.add_edge('select_activities', END)

graph = builder.compile()




if __name__ == '__main__':
    try:
        # Generate the image data
        png_data = graph.get_graph().draw_mermaid_png()

        # Write to a file
        with open("graph_output.png", "wb") as f:
            f.write(png_data)

        print("Success! Graph saved as 'graph_output.png' in your project directory.")
    except Exception as e:
        print(f"Could not generate graph: {e}")
