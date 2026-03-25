from langgraph.graph import START, END, StateGraph

from app.services.activity_suggestion.state import RecommendationState

# Import all nodes
from app.services.activity_suggestion.nodes.select_activities import get_activity_suggestions
from app.services.activity_suggestion.nodes.reconcile_patterns import get_user_patterns
from app.services.activity_suggestion.nodes.process_inputs import process_inputs
from app.services.activity_suggestion.nodes.activity_list import (
    get_activity_library,
    fetch_suggestion_history,
    filter_cooldown_activities,
    format_activity_list
)
from app.services.activity_suggestion.nodes.daily_prompt import (
    get_recent_journals,
    format_journals_for_llm,
    generate_journal_prompt
)

# Define the graph
builder = StateGraph(RecommendationState)

######################################
# Input processing & starting of graph
######################################
builder.add_node('process_inputs', process_inputs)

builder.add_edge(START, 'process_inputs')

######################################
# Activity library pre-processsing & filtering
######################################
builder.add_node('get_activity_library', get_activity_library)
builder.add_node('fetch_suggestion_history', fetch_suggestion_history)
builder.add_node('filter_cooldown_activities', filter_cooldown_activities)
builder.add_node('format_activity_list', format_activity_list)

builder.add_edge('process_inputs', 'get_activity_library')
builder.add_edge('get_activity_library', 'filter_cooldown_activities')
builder.add_edge('process_inputs', 'fetch_suggestion_history')
builder.add_edge('fetch_suggestion_history', 'filter_cooldown_activities')
builder.add_edge('filter_cooldown_activities', 'format_activity_list')
builder.add_edge('format_activity_list', END)


######################################
# User pattern reconcilation
######################################
builder.add_node('get_user_patterns', get_user_patterns)

builder.add_edge('process_inputs', 'get_user_patterns')
builder.add_edge('get_user_patterns', 'select_activities')

######################################
# AI selection of activities
######################################
builder.add_node('select_activities', get_activity_suggestions, defer=True)

builder.add_edge('format_activity_list', 'select_activities')
builder.add_edge('select_activities', END)


#####################################
# Prompt of the day branch
#####################################
builder.add_node('get_recent_journals', get_recent_journals)
builder.add_node('format_journals', format_journals_for_llm)
builder.add_node('generate_journal_prompt', generate_journal_prompt)

builder.add_edge('process_inputs', 'get_recent_journals')
builder.add_edge('get_recent_journals', 'format_journals')
builder.add_edge('format_journals', 'generate_journal_prompt')
builder.add_edge('generate_journal_prompt', END)


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

    # import uuid
    # from app.core.context import request_id_context
    #
    # # 1. Generate a unique ID
    # request_id = str(uuid.uuid4())
    #
    # # 2. Set the context (returns a token used for cleanup)
    # token = request_id_context.set(request_id)
    #
    # try:
    #     # 3. Proceed to the router/service
    #     state = RecommendationState(
    #         user_id=237101,
    #         user_mood='happy',
    #         user_goal='awareness',
    #         is_premium=0,
    #         routine_length='10-15'
    #     )
    #     import asyncio
    #
    #     response = asyncio.run(graph.ainvoke(state))
    #     print(response)
    # finally:
    #     # 4. Clean up the context after the request is done
    #     request_id_context.reset(token)
