# Agno - Migration

**Pages:** 6

---

## How to get the token and chat_id:

**URL:** llms-txt#how-to-get-the-token-and-chat_id:

---

## How to connect to an Upstash Vector index

**URL:** llms-txt#how-to-connect-to-an-upstash-vector-index

---

## Define how to turn analysis into actionable insights

**URL:** llms-txt#define-how-to-turn-analysis-into-actionable-insights

**Contents:**
  - 3d. Define the Report Format

intelligence_synthesis = dedent("""
    INTELLIGENCE SYNTHESIS:
    - Detect crisis indicators through sentiment velocity and coordination patterns
    - Identify competitive positioning and feature gap discussions
    - Surface growth opportunities and advocacy moments
    - Generate strategic recommendations with clear priority levels
""")

print("Intelligence synthesis defined")
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### 3d. Define the Report Format
```

---

## How to Switch Between Different Models

**URL:** llms-txt#how-to-switch-between-different-models

**Contents:**
- Recommended Approach
- Safe Model Switching

Source: https://docs.agno.com/faq/switching-models

When working with Agno, you may need to switch between different models. While Agno supports 20+ model providers, switching between different providers can cause compatibility issues. Switching models within the same provider is generally safer and more reliable.

## Recommended Approach

**Safe:** Switch models within the same provider (OpenAI → OpenAI, Google → Google)\
**Risky:** Switch between different providers (OpenAI ↔ Google ↔ Anthropic)

Cross-provider switching is risky because message history between model providers are often not interchangeable, as some require messages that others don't. However, we are actively working to improve interoperability.

## Safe Model Switching

The safest way to switch models is to change the model ID while keeping the same provider:

```python  theme={null}
from uuid import uuid4
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai.chat import OpenAIChat

db = SqliteDb(db_file="tmp/agent_sessions.db")

session_id = str(uuid4())
user_id = "user@example.com"

---

## Migrating to Agno v2.0

**URL:** llms-txt#migrating-to-agno-v2.0

**Contents:**
- Installing Agno v2
- Migrating your Agno DB
- Migrating your Agno code
  - 1. Agents and Teams
  - 2. Storage

Source: https://docs.agno.com/how-to/v2-migration

Guide to migrate your Agno applications from v1 to v2.

If you have questions during your migration, we can help! Find us on [Discord](https://discord.gg/4MtYHHrgA8) or [Discourse](https://community.agno.com/).

<Tip>
  Reference the [v2.0 Changelog](/how-to/v2-changelog) for the full list of
  changes.
</Tip>

## Installing Agno v2

If you are already using Agno, you can upgrade to v2 by running:

Otherwise, you can install the latest version of Agno v2 by running:

## Migrating your Agno DB

If you used our `Storage` or `Memory` functionalities to store Agent sessions and memories in your database, you can start by migrating your tables.

Use our migration script: [`libs/agno/scripts/migrate_to_v2.py`](https://github.com/agno-agi/agno/blob/main/libs/agno/scripts/migrate_to_v2.py)

The script supports PostgreSQL, MySQL, SQLite, and MongoDB. Update the database connection settings, the batch size (useful if you are migrating large tables) in the script and run it.

* The script won't cleanup the old tables, in case you still need them.
* The script is idempotent. If something goes wrong or if you stop it mid-run, you can run it again.
* Metrics are automatically converted from v1 to v2 format.

## Migrating your Agno code

Each section here covers a specific framework domain, with before and after examples and detailed explanations where needed.

### 1. Agents and Teams

[Agents](/concepts/agents/overview) and [Teams](/concepts/teams/overview) are the main building blocks in the Agno framework.

Below are some of the v2 updates we have made to the `Agent` and `Team` classes:

1.1. Streaming responses with `arun` now returns an `AsyncIterator`, not a coroutine. This is how you consume the resulting events now, when streaming a run:

1.2. The `RunResponse` class is now `RunOutput`. This is the type of the results you get when running an Agent:

1.3. The events you get when streaming an Agent result have been renamed:

* `RunOutputStartedEvent` → `RunStartedEvent`
* `RunOutputCompletedEvent` → `RunCompletedEvent`
* `RunOutputErrorEvent` → `RunErrorEvent`
* `RunOutputCancelledEvent` → `RunCancelledEvent`
* `RunOutputContinuedEvent` → `RunContinuedEvent`
* `RunOutputPausedEvent` → `RunPausedEvent`
* `RunOutputContentEvent` → `RunContentEvent`

1.4. Similarly, for Team output events:

* `TeamRunOutputStartedEvent` → `TeamRunStartedEvent`
* `TeamRunOutputCompletedEvent` → `TeamRunCompletedEvent`
* `TeamRunOutputErrorEvent` → `TeamRunErrorEvent`
* `TeamRunOutputCancelledEvent` → `TeamRunCancelledEvent`
* `TeamRunOutputContentEvent` → `TeamRunContentEvent`

1.5. The `add_state_in_messages` parameter has been deprecated. Variables in instructions are now resolved automatically by default.
1.6. The `context` parameter has been renamed to `dependencies`.

This is how it looked like on v1:

This is how it looks like now, on v2:

<Tip>
  See the full list of changes in the [Agent
  Updates](/how-to/v2-changelog#agent-updates) section of the changelog.
</Tip>

Storage is used to persist Agent sessions, state and memories in a database.

This is how Storage looks like on v1:

These are the changes we have made for v2:

2.1. The `Storage` classes have moved from `agno/storage` to `agno/db`. We will now refer to them as our `Db` classes.
2.2. The `mode` parameter has been deprecated. The same instance can now be used by Agents, Teams and Workflows.

2.3. The `table_name` parameter has been deprecated. One instance now handles multiple tables, you can define their names individually.

These are all the supported tables, each used to persist data related to a specific domain:

2.4. Previously running a `Team` would create a team session and sessions for every team member participating in the run. Now, only the `Team` session is created. The runs for the team leader and all members can be found in the `Team` session.

```python v2_storage_team_sessions.py theme={null}
team.run(...)

team_session = team.get_latest_session()

**Examples:**

Example 1 (unknown):
```unknown
Otherwise, you can install the latest version of Agno v2 by running:
```

Example 2 (unknown):
```unknown
## Migrating your Agno DB

If you used our `Storage` or `Memory` functionalities to store Agent sessions and memories in your database, you can start by migrating your tables.

Use our migration script: [`libs/agno/scripts/migrate_to_v2.py`](https://github.com/agno-agi/agno/blob/main/libs/agno/scripts/migrate_to_v2.py)

The script supports PostgreSQL, MySQL, SQLite, and MongoDB. Update the database connection settings, the batch size (useful if you are migrating large tables) in the script and run it.

Notice:

* The script won't cleanup the old tables, in case you still need them.
* The script is idempotent. If something goes wrong or if you stop it mid-run, you can run it again.
* Metrics are automatically converted from v1 to v2 format.

## Migrating your Agno code

Each section here covers a specific framework domain, with before and after examples and detailed explanations where needed.

### 1. Agents and Teams

[Agents](/concepts/agents/overview) and [Teams](/concepts/teams/overview) are the main building blocks in the Agno framework.

Below are some of the v2 updates we have made to the `Agent` and `Team` classes:

1.1. Streaming responses with `arun` now returns an `AsyncIterator`, not a coroutine. This is how you consume the resulting events now, when streaming a run:
```

Example 3 (unknown):
```unknown
1.2. The `RunResponse` class is now `RunOutput`. This is the type of the results you get when running an Agent:
```

Example 4 (unknown):
```unknown
1.3. The events you get when streaming an Agent result have been renamed:

* `RunOutputStartedEvent` → `RunStartedEvent`
* `RunOutputCompletedEvent` → `RunCompletedEvent`
* `RunOutputErrorEvent` → `RunErrorEvent`
* `RunOutputCancelledEvent` → `RunCancelledEvent`
* `RunOutputContinuedEvent` → `RunContinuedEvent`
* `RunOutputPausedEvent` → `RunPausedEvent`
* `RunOutputContentEvent` → `RunContentEvent`

1.4. Similarly, for Team output events:

* `TeamRunOutputStartedEvent` → `TeamRunStartedEvent`
* `TeamRunOutputCompletedEvent` → `TeamRunCompletedEvent`
* `TeamRunOutputErrorEvent` → `TeamRunErrorEvent`
* `TeamRunOutputCancelledEvent` → `TeamRunCancelledEvent`
* `TeamRunOutputContentEvent` → `TeamRunContentEvent`

1.5. The `add_state_in_messages` parameter has been deprecated. Variables in instructions are now resolved automatically by default.
1.6. The `context` parameter has been renamed to `dependencies`.

This is how it looked like on v1:
```

---

## Migrating to Workflows 2.0

**URL:** llms-txt#migrating-to-workflows-2.0

**Contents:**
- Migrating from Workflows 1.0
  - Key Differences
  - Migration Steps
  - Example of Blog Post Generator Workflow

Source: https://docs.agno.com/how-to/workflows-migration

Learn how to migrate to Workflows 2.0.

## Migrating from Workflows 1.0

Workflows 2.0 is a completely new approach to agent automation, and requires an upgrade from the Workflows 1.0 implementation. It introduces a new, more flexible and powerful way to build workflows.

| Workflows 1.0     | Workflows 2.0     | Migration Path                   |
| ----------------- | ----------------- | -------------------------------- |
| Linear only       | Multiple patterns | Add Parallel/Condition as needed |
| Agent-focused     | Mixed components  | Convert functions to Steps       |
| Limited branching | Smart routing     | Replace if/else with Router      |
| Manual loops      | Built-in Loop     | Use Loop component               |

1. **Assess current workflow**: Identify parallel opportunities
2. **Add conditions**: Convert if/else logic to Condition components
3. **Extract functions**: Move custom logic to function-based steps
4. **Enable streaming**: For event-based information
5. **Add state management**: Use `workflow_session_state` for data sharing

### Example of Blog Post Generator Workflow

Lets take an example that demonstrates how to build a sophisticated blog post generator that combines
web research capabilities with professional writing expertise. The workflow uses a multi-stage
approach:

1. Intelligent web research and source gathering
2. Content extraction and processing
3. Professional blog post writing with proper citations

Here's the code for the blog post generator in **Workflows 1.0**:

```python  theme={null}
import json
from textwrap import dedent
from typing import Dict, Iterator, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.workflow import WorkflowCompletedEvent
from agno.storage.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import RunOutput, Workflow
from pydantic import BaseModel, Field

class NewsArticle(BaseModel):
    title: str = Field(..., description="Title of the article.")
    url: str = Field(..., description="Link to the article.")
    summary: Optional[str] = Field(
        ..., description="Summary of the article if available."
    )

class SearchResults(BaseModel):
    articles: list[NewsArticle]

class ScrapedArticle(BaseModel):
    title: str = Field(..., description="Title of the article.")
    url: str = Field(..., description="Link to the article.")
    summary: Optional[str] = Field(
        ..., description="Summary of the article if available."
    )
    content: Optional[str] = Field(
        ...,
        description="Full article content in markdown format. None if content is unavailable.",
    )

class BlogPostGenerator(Workflow):
    """Advanced workflow for generating professional blog posts with proper research and citations."""

description: str = dedent("""\
    An intelligent blog post generator that creates engaging, well-researched content.
    This workflow orchestrates multiple AI agents to research, analyze, and craft
    compelling blog posts that combine journalistic rigor with engaging storytelling.
    The system excels at creating content that is both informative and optimized for
    digital consumption.
    """)

# Search Agent: Handles intelligent web searching and source gathering
    searcher: Agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[DuckDuckGoTools()],
        description=dedent("""\
        You are BlogResearch-X, an elite research assistant specializing in discovering
        high-quality sources for compelling blog content. Your expertise includes:

- Finding authoritative and trending sources
        - Evaluating content credibility and relevance
        - Identifying diverse perspectives and expert opinions
        - Discovering unique angles and insights
        - Ensuring comprehensive topic coverage\
        """),
        instructions=dedent("""\
        1. Search Strategy 🔍
           - Find 10-15 relevant sources and select the 5-7 best ones
           - Prioritize recent, authoritative content
           - Look for unique angles and expert insights
        2. Source Evaluation 📊
           - Verify source credibility and expertise
           - Check publication dates for timeliness
           - Assess content depth and uniqueness
        3. Diversity of Perspectives 🌐
           - Include different viewpoints
           - Gather both mainstream and expert opinions
           - Find supporting data and statistics\
        """),
        output_schema=SearchResults,
    )

# Content Scraper: Extracts and processes article content
    article_scraper: Agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[Newspaper4kTools()],
        description=dedent("""\
        You are ContentBot-X, a specialist in extracting and processing digital content
        for blog creation. Your expertise includes:

- Efficient content extraction
        - Smart formatting and structuring
        - Key information identification
        - Quote and statistic preservation
        - Maintaining source attribution\
        """),
        instructions=dedent("""\
        1. Content Extraction 📑
           - Extract content from the article
           - Preserve important quotes and statistics
           - Maintain proper attribution
           - Handle paywalls gracefully
        2. Content Processing 🔄
           - Format text in clean markdown
           - Preserve key information
           - Structure content logically
        3. Quality Control ✅
           - Verify content relevance
           - Ensure accurate extraction
           - Maintain readability\
        """),
        output_schema=ScrapedArticle,
    )

# Content Writer Agent: Crafts engaging blog posts from research
    writer: Agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        description=dedent("""\
        You are BlogMaster-X, an elite content creator combining journalistic excellence
        with digital marketing expertise. Your strengths include:

- Crafting viral-worthy headlines
        - Writing engaging introductions
        - Structuring content for digital consumption
        - Incorporating research seamlessly
        - Optimizing for SEO while maintaining quality
        - Creating shareable conclusions\
        """),
        instructions=dedent("""\
        1. Content Strategy 📝
           - Craft attention-grabbing headlines
           - Write compelling introductions
           - Structure content for engagement
           - Include relevant subheadings
        2. Writing Excellence ✍️
           - Balance expertise with accessibility
           - Use clear, engaging language
           - Include relevant examples
           - Incorporate statistics naturally
        3. Source Integration 🔍
           - Cite sources properly
           - Include expert quotes
           - Maintain factual accuracy
        4. Digital Optimization 💻
           - Structure for scanability
           - Include shareable takeaways
           - Optimize for SEO
           - Add engaging subheadings\
        """),
        expected_output=dedent("""\
        # {Viral-Worthy Headline}

## Introduction
        {Engaging hook and context}

## {Compelling Section 1}
        {Key insights and analysis}
        {Expert quotes and statistics}

## {Engaging Section 2}
        {Deeper exploration}
        {Real-world examples}

## {Practical Section 3}
        {Actionable insights}
        {Expert recommendations}

## Key Takeaways
        - {Shareable insight 1}
        - {Practical takeaway 2}
        - {Notable finding 3}

## Sources
        {Properly attributed sources with links}\
        """),
        markdown=True,
    )

def run(
        self,
        topic: str,
        use_search_cache: bool = True,
        use_scrape_cache: bool = True,
        use_cached_report: bool = True,
    ) -> Iterator[RunOutputEvent]:
        logger.info(f"Generating a blog post on: {topic}")

# Use the cached blog post if use_cache is True
        if use_cached_report:
            cached_blog_post = self.get_cached_blog_post(topic)
            if cached_blog_post:
                yield WorkflowCompletedEvent(
                    run_id=self.run_id,
                    content=cached_blog_post,
                )
                return

# Search the web for articles on the topic
        search_results: Optional[SearchResults] = self.get_search_results(
            topic, use_search_cache
        )
        # If no search_results are found for the topic, end the workflow
        if search_results is None or len(search_results.articles) == 0:
            yield WorkflowCompletedEvent(
                run_id=self.run_id,
                content=f"Sorry, could not find any articles on the topic: {topic}",
            )
            return

# Scrape the search results
        scraped_articles: Dict[str, ScrapedArticle] = self.scrape_articles(
            topic, search_results, use_scrape_cache
        )

# Prepare the input for the writer
        writer_input = {
            "topic": topic,
            "articles": [v.model_dump() for v in scraped_articles.values()],
        }

# Run the writer and yield the response
        yield from self.writer.run(json.dumps(writer_input, indent=4), stream=True)

# Save the blog post in the cache
        self.add_blog_post_to_cache(topic, self.writer.run_response.content)

def get_cached_blog_post(self, topic: str) -> Optional[str]:
        logger.info("Checking if cached blog post exists")

return self.session_state.get("blog_posts", {}).get(topic)

def add_blog_post_to_cache(self, topic: str, blog_post: str):
        logger.info(f"Saving blog post for topic: {topic}")
        self.session_state.setdefault("blog_posts", {})
        self.session_state["blog_posts"][topic] = blog_post

def get_cached_search_results(self, topic: str) -> Optional[SearchResults]:
        logger.info("Checking if cached search results exist")
        search_results = self.session_state.get("search_results", {}).get(topic)
        return (
            SearchResults.model_validate(search_results)
            if search_results and isinstance(search_results, dict)
            else search_results
        )

def add_search_results_to_cache(self, topic: str, search_results: SearchResults):
        logger.info(f"Saving search results for topic: {topic}")
        self.session_state.setdefault("search_results", {})
        self.session_state["search_results"][topic] = search_results

def get_cached_scraped_articles(
        self, topic: str
    ) -> Optional[Dict[str, ScrapedArticle]]:
        logger.info("Checking if cached scraped articles exist")
        scraped_articles = self.session_state.get("scraped_articles", {}).get(topic)
        return (
            ScrapedArticle.model_validate(scraped_articles)
            if scraped_articles and isinstance(scraped_articles, dict)
            else scraped_articles
        )

def add_scraped_articles_to_cache(
        self, topic: str, scraped_articles: Dict[str, ScrapedArticle]
    ):
        logger.info(f"Saving scraped articles for topic: {topic}")
        self.session_state.setdefault("scraped_articles", {})
        self.session_state["scraped_articles"][topic] = scraped_articles

def get_search_results(
        self, topic: str, use_search_cache: bool, num_attempts: int = 3
    ) -> Optional[SearchResults]:
        # Get cached search_results from the session state if use_search_cache is True
        if use_search_cache:
            try:
                search_results_from_cache = self.get_cached_search_results(topic)
                if search_results_from_cache is not None:
                    search_results = SearchResults.model_validate(
                        search_results_from_cache
                    )
                    logger.info(
                        f"Found {len(search_results.articles)} articles in cache."
                    )
                    return search_results
            except Exception as e:
                logger.warning(f"Could not read search results from cache: {e}")

# If there are no cached search_results, use the searcher to find the latest articles
        for attempt in range(num_attempts):
            try:
                searcher_response: RunOutput = self.searcher.run(topic)
                if (
                    searcher_response is not None
                    and searcher_response.content is not None
                    and isinstance(searcher_response.content, SearchResults)
                ):
                    article_count = len(searcher_response.content.articles)
                    logger.info(
                        f"Found {article_count} articles on attempt {attempt + 1}"
                    )
                    # Cache the search results
                    self.add_search_results_to_cache(topic, searcher_response.content)
                    return searcher_response.content
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}/{num_attempts} failed: Invalid response type"
                    )
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{num_attempts} failed: {str(e)}")

logger.error(f"Failed to get search results after {num_attempts} attempts")
        return None

def scrape_articles(
        self, topic: str, search_results: SearchResults, use_scrape_cache: bool
    ) -> Dict[str, ScrapedArticle]:
        scraped_articles: Dict[str, ScrapedArticle] = {}

# Get cached scraped_articles from the session state if use_scrape_cache is True
        if use_scrape_cache:
            try:
                scraped_articles_from_cache = self.get_cached_scraped_articles(topic)
                if scraped_articles_from_cache is not None:
                    scraped_articles = scraped_articles_from_cache
                    logger.info(
                        f"Found {len(scraped_articles)} scraped articles in cache."
                    )
                    return scraped_articles
            except Exception as e:
                logger.warning(f"Could not read scraped articles from cache: {e}")

# Scrape the articles that are not in the cache
        for article in search_results.articles:
            if article.url in scraped_articles:
                logger.info(f"Found scraped article in cache: {article.url}")
                continue

article_scraper_response: RunOutput = self.article_scraper.run(
                article.url
            )
            if (
                article_scraper_response is not None
                and article_scraper_response.content is not None
                and isinstance(article_scraper_response.content, ScrapedArticle)
            ):
                scraped_articles[article_scraper_response.content.url] = (
                    article_scraper_response.content
                )
                logger.info(f"Scraped article: {article_scraper_response.content.url}")

# Save the scraped articles in the session state
        self.add_scraped_articles_to_cache(topic, scraped_articles)
        return scraped_articles

---
