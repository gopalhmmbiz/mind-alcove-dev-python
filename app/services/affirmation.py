from langchain.messages import SystemMessage, HumanMessage

from app.ai.models import llm
from app.ai.prompts.affirmation import SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE
from app.ai.structured_outputs.affirmation import Affirmations
from app.api.schemas.affirmation import (
    AffirmationRequest,
    AffirmationResponse,
)


async def generate_affirmations_service(
    payload: AffirmationRequest,
) -> AffirmationResponse:
    """
    Generate affirmations using LLM based on user input.
    """

    # Prepare user message
    formatted_user_message = USER_MESSAGE_TEMPLATE.format(
        user_goal=payload.user_goal,
        overall_goal=payload.overall_goal,
        mood=payload.mood,
        emotion=payload.emotion,
    )

    messages = [
        SystemMessage(SYSTEM_MESSAGE),
        HumanMessage(formatted_user_message),
    ]

    # Bind structured output
    structured_llm = llm.with_structured_output(Affirmations)

    # Invoke model asynchronously
    response = await structured_llm.ainvoke(messages)

    # Map structured output to API response
    return AffirmationResponse(
        affirmation_one=response.affirmation_one,
        affirmation_two=response.affirmation_two,
        affirmation_three=response.affirmation_three,
    )
