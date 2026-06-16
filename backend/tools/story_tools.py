from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI


@tool
def refine_story(description: str) -> str:
    """Refine a user story description into a well-structured format with acceptance criteria."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
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
    return llm.invoke(prompt).content


@tool
def split_story(story_text: str) -> str:
    """Split a large user story into smaller, independent sub-stories."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    prompt = f"""Split this user story into smaller independent stories:

{story_text}

Return each sub-story as:
- Story 1: As a... I want... so that...
- Story 2: ..."""
    return llm.invoke(prompt).content


@tool
def estimate_effort(story_text: str) -> str:
    """Estimate effort for a user story in story points (Fibonacci: 1, 2, 3, 5, 8, 13)."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
    prompt = f"""Estimate the effort for this user story in Fibonacci story points (1, 2, 3, 5, 8, 13):

{story_text}

Consider: complexity, unknowns, dependencies, testing needs.

Return: 'Estimated effort: X story points' with a brief justification."""
    return llm.invoke(prompt).content


story_tools = [refine_story, split_story, estimate_effort]
