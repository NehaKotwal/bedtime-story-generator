# Bedtime Story Generator

Generates quality bedtime stories for children using an LLM judge to ensure stories meet standards before delivery.

## Architecture

```
Request → Generate → Judge → [Refine if <7] → Deliver
                       ↑__________|  (max 1x)
```

**Components:**
- **Generator** - Creates stories with appropriate vocabulary, wind-down pacing
- **Judge** - Chain-of-thought evaluation on: request adherence, age-appropriateness, engagement, pacing, moral, safety
- **Refiner** - Fixes specific issues identified by judge

## Usage

```bash
export OPENAI_API_KEY="..."
python main.py
```

**Moods:** calm (default), adventurous, silly, cozy
```
Story request: a bunny who finds a friend --mood cozy
```

## Sample Output

```
=============================
  Bedtime Story Generator
=============================

Moods: calm (default), adventurous, silly, cozy
Example: 'a story about a bunny --mood silly'
(Type 'quit' to exit, 'new' for a different story)

Story request: a bunny who finds a friend --mood silly

Generating story for: "a bunny who finds a friend" [mood: silly]

Attempt 1: Score 9/10
=============================
Once upon a time in a cozy meadow, there lived a little bunny named Berry. Berry loved hopping around, sniffing flowers, and nibbling on juicy carrots. But deep down, Berry felt a little lonely. All the other bunnies in the meadow seemed to have friends to play with, and Berry wished for a friend too.

One sunny morning, as Berry hopped along a winding path, a soft voice called out, "Hello there! I'm Willow, the friendly squirrel. What's your name?" Berry's ears perked up, and a big smile spread across Berry's face. "I'm Berry the bunny! Nice to meet you, Willow," Berry replied cheerfully.

From that day on, Berry and Willow became the best of friends. They played tag among the tall trees, shared stories under the shimmering moonlight, and even had picnics with berries and acorns. Berry felt happier than ever before, knowing that there was someone as kind and fun as Willow by their side.

One day, as they were playing hide-and-seek, Berry got a little too excited and hopped too far ahead. Soon, Berry found themselves lost in the maze of bushes and tall grass. "Oh no, where am I?" Berry called out, feeling a bit scared. Willow heard Berry's voice and hurried over. "Don't worry, Berry! I'll help you find your way back," reassured Willow with a comforting smile.

Together, Berry and Willow followed the scent of wildflowers and the sound of chirping birds until they reached the familiar meadow. Berry felt grateful for having such a caring friend like Willow. "Thank you for helping me, Willow. I'm so lucky to have you as my friend," said Berry, nuzzling Willow gently.

As the sun started to set, casting a warm glow over the meadow, Berry and Willow sat side by side, watching the fireflies dance in the evening sky. "I'm glad we found each other, Berry. Friends help each other through thick and thin," Willow said, patting Berry's furry paw. Berry nodded, feeling a deep sense of contentment.

With a yawn, Berry and Willow decided it was time to head back to their burrows. As they said their goodnights and curled up in their cozy nests, Berry whispered, "Goodnight, Willow. I'm so grateful for your friendship." Willow whispered back, "Sweet dreams, Berry. Friends forever."

And so, under the twinkling stars and the watchful moon, Berry drifted off to sleep, feeling loved, happy, and grateful for the wonderful friend they had found in Willow. The gentle rustle of the leaves and the soft hoot of an owl lulled them into a peaceful slumber, knowing that friendship was the most precious treasure of all. Goodnight, Berry and Willow. Goodnight.
=============================

Score: 9/10 | ~4 min read

Changes? (or 'new'/'quit'): 
```

## Block Diagram

```
USER  "story about a brave rabbit --mood adventurous"
  │
GENERATOR ────────────────────────────────────────
  [mood + safety boundaries + wind-down pacing]
  -> 400-500 word story
  │
JUDGE ────────────────────────────────────────────
  Chain-of-thought: evaluates each criterion
  -> { score: 7, feedback: [...], approved: true }
  │
  ├── score < 7 ── REFINER ── (loop, max 1x)
  │
  └── score >= 7 ── OUTPUT + reading time
                         │
                    USER can request changes
```