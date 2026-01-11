"""
Bedtime Story Generator with LLM Judge
Hippocratic AI Take-Home Assessment

If I had 2 more hours, I would:
- Add a "story memory" system that remembers characters/themes a child likes
- Build a simple web UI with Flask for easier parent interaction  
- Implement voice output using a TTS API for actual bedtime reading
- Add illustration prompts that could feed into an image generator
"""

import os
import json
import time
from openai import OpenAI
from dataclasses import dataclass

# Story moods - affects tone and pacing
MOODS = {
    "calm": "Use a slow, soothing pace. Extra gentle. Good for anxious kids or late nights.",
    "adventurous": "More excitement and action, but still end peacefully.",
    "silly": "Include humor and funny moments. Light and playful.",
    "cozy": "Focus on warmth, comfort, and safe feelings. Lots of sensory details."
}

# Content we never generate (safety boundaries for a healthcare AI company)
SAFETY_BOUNDARIES = """
Never include:
- Medical advice or health decisions
- Scary elements (monsters, danger, death, being lost/abandoned)
- Violence or conflict beyond mild disagreements
- Complex emotions like grief, divorce, serious illness
- Anything that could increase bedtime anxiety
"""

# Initialize client once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(messages: list, temperature: float = 0.7, max_tokens: int = 2000, retries: int = 3) -> str:
    """Core LLM call with retry logic for transient failures."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
                continue
            raise RuntimeError(f"API call failed after {retries} attempts: {e}")


@dataclass
class StoryEvaluation:
    score: int
    feedback: list
    approved: bool


# --- Prompts live here for easy tuning ---

STORY_SYSTEM_PROMPT = """You write bedtime stories for children ages 5-10.

Your stories:
- Use simple words but aren't boring
- Have a clear beginning, middle, and end
- Include dialogue between characters
- Teach a gentle lesson without being preachy
- End calmly so kids can drift off to sleep
- Pace gets slower and more soothing toward the end (wind-down effect)
{mood_instruction}
{safety}
Length: About 400-500 words. No headers or formatting - just the story."""


JUDGE_SYSTEM_PROMPT = """You evaluate children's bedtime stories. Be constructive but honest.

First, think through each criterion, then score:
1. Request adherence - does it match what was asked for? characters, setting, theme?
2. Age-appropriateness - nothing scary, vocabulary fits 5-10 year olds?
3. Engagement - would a kid stay interested?
4. Pacing - right length, builds then resolves tension, calms down at end?
5. Lesson - has a gentle moral woven in naturally?
6. Safety - no medical advice, nothing anxiety-inducing, no scary elements?

After evaluating each, give an overall score 1-10.

Respond in JSON:
{
    "thinking": "brief evaluation of each criterion",
    "score": <1-10>,
    "feedback": ["specific issue 1", "specific issue 2"],
    "approved": <true if score >= 7>
}

Be specific in feedback - vague comments don't help improve the story."""


REFINE_SYSTEM_PROMPT = """You improve children's bedtime stories based on feedback.

Keep the same characters and basic plot. Focus only on the specific issues raised.
Don't add headers or meta-commentary - just output the improved story."""


def generate_story(request: str, mood: str = "calm") -> str:
    """Generate initial story from user request."""
    mood_instruction = MOODS.get(mood, MOODS["calm"])
    system = STORY_SYSTEM_PROMPT.format(
        mood_instruction=f"\nMood: {mood_instruction}",
        safety=SAFETY_BOUNDARIES
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Write a bedtime story based on this request: {request}"}
    ]
    return call_llm(messages, temperature=0.85)


def estimate_reading_time(text: str) -> str:
    """Estimate reading time for bedtime (slower pace ~120 wpm)."""
    words = len(text.split())
    minutes = round(words / 120)
    return f"~{max(1, minutes)} min read"


def judge_story(story: str, original_request: str) -> StoryEvaluation:
    """LLM judge evaluates the story quality using chain-of-thought."""
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Original request: {original_request}\n\nStory to evaluate:\n{story}"}
    ]
    
    response = call_llm(messages, temperature=0.3)
    
    # Parse JSON from response
    try:
        # Handle cases where model wraps JSON in markdown
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        
        data = json.loads(clean)
        return StoryEvaluation(
            score=data.get("score", 5),
            feedback=data.get("feedback", []),
            approved=data.get("approved", False)
        )
    except json.JSONDecodeError:
        return StoryEvaluation(score=5, feedback=["Could not parse evaluation"], approved=False)


def refine_story(story: str, feedback: list) -> str:
    """Improve story based on judge feedback."""
    feedback_text = "\n".join(f"- {item}" for item in feedback)
    
    messages = [
        {"role": "system", "content": REFINE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Feedback to address:\n{feedback_text}\n\nOriginal story:\n{story}"}
    ]
    return call_llm(messages, temperature=0.75)


def apply_user_feedback(story: str, user_feedback: str) -> str:
    """Modify story based on user's requested changes."""
    messages = [
        {"role": "system", "content": REFINE_SYSTEM_PROMPT},
        {"role": "user", "content": f"User requested this change: {user_feedback}\n\nCurrent story:\n{story}"}
    ]
    return call_llm(messages, temperature=0.7)


def create_story(request: str, mood: str = "calm", max_attempts: int = 1, verbose: bool = True) -> tuple[str, StoryEvaluation]:
    """
    Main pipeline: generate -> judge -> refine loop.
    
    Returns (final_story, final_evaluation)
    """
    if verbose:
        print(f"\nGenerating story for: \"{request}\" [mood: {mood}]\n")
    
    story = generate_story(request, mood=mood)
    
    for attempt in range(max_attempts):
        evaluation = judge_story(story, request)
        
        if verbose:
            print(f"Attempt {attempt + 1}: Score {evaluation.score}/10")
            if evaluation.feedback:
                print(f"  Feedback: {evaluation.feedback[0]}")
        
        if evaluation.approved:
            break
            
        if attempt < max_attempts - 1:
            story = refine_story(story, evaluation.feedback)
    
    return story, evaluation


def interactive_session():
    """Run an interactive story session with feedback loop."""
    print("=============================")
    print("  Bedtime Story Generator")
    print("=============================")
    print("\nMoods: calm (default), adventurous, silly, cozy")
    print("Example: 'a story about a bunny --mood silly'")
    print("(Type 'quit' to exit, 'new' for a different story)\n")
    
    current_story = None
    
    while True:
        if current_story is None:
            user_input = input("Story request: ").strip()
        else:
            user_input = input("\nChanges? (or 'new'/'quit'): ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            print("\nSweet dreams!\n")
            break
        
        if user_input.lower() == 'new':
            current_story = None
            print("\nWhat story would you like?\n")
            continue
        
        if current_story is None:
            # Parse mood from request
            mood = "calm"
            request = user_input
            if "--mood" in user_input:
                parts = user_input.split("--mood")
                request = parts[0].strip()
                mood_arg = parts[1].strip().split()[0] if parts[1].strip() else "calm"
                if mood_arg in MOODS:
                    mood = mood_arg
            
            current_story, evaluation = create_story(request, mood=mood)
            
            print("=============================")
            print(current_story)
            print("=============================")
            print(f"\nScore: {evaluation.score}/10 | {estimate_reading_time(current_story)}")
        else:
            # Apply user feedback
            print("\nUpdating story...")
            current_story = apply_user_feedback(current_story, user_input)
            
            print("=============================")
            print(current_story)
            print("=============================")
            print(f"\n{estimate_reading_time(current_story)}")


def main():
    """Entry point - can run interactive or with a single request."""
    import sys
    
    if len(sys.argv) > 1:
        # Single request mode
        request = " ".join(sys.argv[1:])
        story, evaluation = create_story(request)
        print("\n" + story)
        print(f"\n[Score: {evaluation.score}/10 | {estimate_reading_time(story)}]")
    else:
        # Interactive mode
        interactive_session()


if __name__ == "__main__":
    main()