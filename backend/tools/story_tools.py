import logging
from langchain_core.tools import tool
from ..agent_graph.llm import create_llm, invoke_with_retry, get_fallback_model_name, is_rate_limited

logger = logging.getLogger("agile_agent.tools.story")


def _invoke_story_llm(llm, prompt):
    return invoke_with_retry(llm, prompt).content


def _story_llm_call(prompt: str, temperature: float = 0.3):
    try:
        llm = create_llm(temperature=temperature)
        return _invoke_story_llm(llm, prompt)
    except Exception as e:
        if is_rate_limited(e):
            fallback_model = get_fallback_model_name()
            if fallback_model:
                try:
                    llm = create_llm(model=fallback_model, temperature=temperature)
                    return _invoke_story_llm(llm, prompt)
                except Exception as e2:
                    logger.error("Fallback LLM also failed: %s", e2)
        raise


@tool
def refine_story(description: str) -> str:
    """Refine a user story description into a well-structured format with acceptance criteria."""
    logger.info("Tool refine_story called — description length=%d", len(description))
    prompt = f"""Refine this user story into a structured format:

Raw description: {description}

Return:
## User Story
As a [user], I want [goal] so that [benefit].

## Acceptance Criteria
1. ...
2. ...

## Technical Notes (if applicable)
- ..."""
    response = _story_llm_call(prompt, temperature=0.3)
    logger.info("refine_story: response length=%d", len(response))
    return response


@tool
def split_story(story_text: str) -> str:
    """Split a large user story into smaller, independent sub-stories."""
    logger.info("Tool split_story called — input length=%d", len(story_text))
    prompt = f"""Split this user story into smaller independent stories:

{story_text}

Return each sub-story as:
- Story 1: As a... I want... so that...
- Story 2: ..."""
    response = _story_llm_call(prompt, temperature=0.3)
    logger.info("split_story: response length=%d", len(response))
    return response


@tool
def estimate_effort(story_text: str) -> str:
    """Estimate effort for a user story in story points (Fibonacci: 1, 2, 3, 5, 8, 13)."""
    logger.info("Tool estimate_effort called — input length=%d", len(story_text))
    prompt = f"""Estimate the effort for this user story in Fibonacci story points (1, 2, 3, 5, 8, 13):

{story_text}

Consider: complexity, unknowns, dependencies, testing needs.

Return: 'Estimated effort: X story points' with a brief justification."""
    response = _story_llm_call(prompt, temperature=0.2)
    logger.info("estimate_effort: response — %s", response[:200])
    return response


story_tools = [refine_story, split_story, estimate_effort]
