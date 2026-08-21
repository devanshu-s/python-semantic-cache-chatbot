import re
import html
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from backend.config.settings import settings
from backend.utils.logger import logger

class LeetCodeProblem(BaseModel):
    title: str
    title_slug: str
    difficulty: str
    description: str
    python_starter_code: str
    example_test_cases: List[str] = []
    formatted_prompt: str

class LeetCodeService:
    GRAPHQL_URL = "https://leetcode.com/graphql"

    def clean_html(self, raw_html: str) -> str:
        """Convert basic LeetCode HTML description into clean readable text/markdown."""
        if not raw_html:
            return ""
        # Replace common tags
        text = raw_html.replace("<p>", "").replace("</p>", "\n\n")
        text = text.replace("<code>", "`").replace("</code>", "`")
        text = text.replace("<pre>", "\n```\n").replace("</pre>", "\n```\n")
        text = text.replace("<strong>", "**").replace("</strong>", "**")
        text = text.replace("<em>", "*").replace("</em>", "*")
        text = text.replace("&nbsp;", " ")
        text = text.replace("&le;", "<=").replace("&ge;", ">=").replace("&lt;", "<").replace("&gt;", ">")
        text = re.sub(r"<li[^>]*>", "- ", text)
        text = text.replace("</li>", "\n")
        text = re.sub(r"<ul[^>]*>", "\n", text).replace("</ul>", "\n")
        text = re.sub(r"<ol[^>]*>", "\n", text).replace("</ol>", "\n")
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        return text.strip()

    def extract_slug(self, url_or_title: str) -> str:
        """Extract title slug from a LeetCode URL or convert title to slug."""
        cleaned = url_or_title.strip()
        
        # Check if URL
        match = re.search(r"leetcode\.com/problems/([a-zA-Z0-9\-]+)", cleaned)
        if match:
            return match.group(1).lower()

        # Else convert title string to slug
        cleaned = re.sub(r"^[0-9]+\.\s*", "", cleaned) # Remove leading number e.g. "1. Two Sum"
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", cleaned)
        slug = re.sub(r"[\s_]+", "-", slug).strip("-").lower()
        return slug

    def fetch_problem(self, url_or_title: str) -> LeetCodeProblem:
        """Fetch problem data from LeetCode GraphQL or fallback to Gemini."""
        slug = self.extract_slug(url_or_title)
        
        try:
            query = """
            query getQuestionDetail($titleSlug: String!) {
              question(titleSlug: $titleSlug) {
                questionId
                title
                titleSlug
                difficulty
                content
                codeSnippets {
                  lang
                  langSlug
                  code
                }
                exampleTestcaseList
              }
            }
            """
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://leetcode.com",
                "Content-Type": "application/json"
            }
            
            res = requests.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": {"titleSlug": slug}},
                headers=headers,
                timeout=8
            )

            if res.status_code == 200:
                data = res.json()
                q = data.get("data", {}).get("question")
                if q and q.get("title"):
                    title = q.get("title")
                    difficulty = q.get("difficulty", "Medium")
                    clean_desc = self.clean_html(q.get("content", ""))
                    
                    # Extract python starter code
                    snippets = q.get("codeSnippets") or []
                    py_code = ""
                    for s in snippets:
                        if s.get("langSlug") == "python3":
                            py_code = s.get("code", "")
                            break
                        elif s.get("langSlug") == "python" and not py_code:
                            py_code = s.get("code", "")

                    if not py_code:
                        py_code = "class Solution:\n    def solve(self):\n        pass\n"

                    examples = q.get("exampleTestcaseList") or []

                    prompt = (
                        f"Solve the LeetCode problem: **{title}** ({difficulty})\n\n"
                        f"### 📝 Problem Description:\n{clean_desc}\n\n"
                        f"### 💻 LeetCode Starter Template:\n```python\n{py_code}\n```\n\n"
                        "Please analyze the problem, provide the Top 10 Test Cases (standard + edge cases) first, "
                        "and then provide the optimal solution in LeetCode `class Solution:` format that passes all 10 test cases."
                    )

                    return LeetCodeProblem(
                        title=title,
                        title_slug=slug,
                        difficulty=difficulty,
                        description=clean_desc,
                        python_starter_code=py_code,
                        example_test_cases=examples,
                        formatted_prompt=prompt
                    )

        except Exception as e:
            logger.warning(f"LeetCode GraphQL fetch failed for {slug}: {e}. Falling back to AI retriever.")

        # Fallback using Gemini
        return self._fetch_via_gemini_fallback(url_or_title, slug)

    def _fetch_via_gemini_fallback(self, query_str: str, slug: str) -> LeetCodeProblem:
        """Use Gemini to retrieve LeetCode problem details when GraphQL endpoint is blocked."""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""
Retrieve the exact specifications for the LeetCode problem matching: "{query_str}" (Slug: {slug}).
Return a valid JSON with:
{{
  "title": "<Exact LeetCode Title, e.g. Two Sum>",
  "difficulty": "<Easy | Medium | Hard>",
  "description": "<Concise Problem statement, input/output specifications, constraints>",
  "python_starter_code": "<Standard LeetCode Python3 class Solution template with type hints>",
  "examples": ["<Example 1 input/output>", "<Example 2 input/output>"]
}}
"""
            config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[prompt],
                config=config
            )

            import json
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            data = json.loads(raw.strip())

            title = data.get("title", query_str.title())
            difficulty = data.get("difficulty", "Medium")
            desc = data.get("description", "")
            py_code = data.get("python_starter_code", "class Solution:\n    def solve(self):\n        pass\n")
            examples = data.get("examples", [])

            formatted = (
                f"Solve the LeetCode problem: **{title}** ({difficulty})\n\n"
                f"### 📝 Problem Description:\n{desc}\n\n"
                f"### 💻 LeetCode Starter Template:\n```python\n{py_code}\n```\n\n"
                "Please provide the Top 10 Test Cases first, followed by the complete optimal solution in LeetCode `class Solution:` style."
            )

            return LeetCodeProblem(
                title=title,
                title_slug=slug,
                difficulty=difficulty,
                description=desc,
                python_starter_code=py_code,
                example_test_cases=examples,
                formatted_prompt=formatted
            )

        except Exception as e:
            logger.error(f"Fallback LeetCode generator error: {e}")
            title = query_str.replace("https://leetcode.com/problems/", "").replace("/", "").replace("-", " ").title()
            default_prompt = f"Solve the LeetCode problem: {title}\nProvide top 10 test cases first and complete optimal class Solution code."
            return LeetCodeProblem(
                title=title,
                title_slug=slug,
                difficulty="Medium",
                description=f"Problem specifications for {title}",
                python_starter_code="class Solution:\n    def solve(self):\n        pass\n",
                example_test_cases=[],
                formatted_prompt=default_prompt
            )
