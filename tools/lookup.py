"""
title: Lookup
author: Raphael Wong
author_url: https://github.com/raphael1-w
description: Search the web for information.
required_open_webui_version: 0.5.0
requirements: httpx, lxml-html-clean
version: 0.9.0
licence: GNU General Public License v3.0
"""

import httpx
from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable, List
import asyncio
import os
import requests
import urllib.parse
import time


class Tools:
    class Valves(BaseModel):
        searxng_url: str = Field(
            "http://localhost:8080",  # Default SearXNG URL
            description="URL of your SearXNG instance (e.g., http://localhost:8080)",
        )
        safesearch: bool = Field(
            False,
            description="Enable SafeSearch filtering",
        )

    def __init__(self):
        """Initialize the Tool."""
        self.valves = self.Valves()
        self.citation = False  # Disable automatic citations

    async def web_search(
        self,
        queries: List[str],
        number_of_results_per_query: int,
        __event_emitter__=None,
    ) -> str:
        """
        Perform Google searches for a list of queries and returns snippets, titles, and links.
        Use multiple searches that are composed of both natural language questions and keyword queries.
        When creating the searches, minimally rephrase the prompt, and if possible do not rephrase it at all.
        For example:
        * "in year 2020 who was the recipient of award X" should result in issuing the following searches: ["who won the X award 2020", "X award year 2020"].
        Issue the natural language questions first, and then the keyword search queries. Try to have at least 1 question and 1 keyword query issued as searches. Use interrogative words when generating the questions for the searches such as "how", "who", "what", etc.

        Number of results per query is between 3 and 8. Use a higher number when more context is needed.
        """
        searxng_url = self.valves.searxng_url
        safesearch = self.valves.safesearch
        if number_of_results_per_query > 8:
            number_of_results_per_query = 8  # Enforce maximum
        if number_of_results_per_query < 1:
            number_of_results_per_query = 1  # enforce minimum number of results.

        output = ""
        search_queries = " | ".join(queries)
        output += f"Success\n"  # Add query context

        tool_tip_content = f"""Search queries: {search_queries}
        Number of results per search queries: {number_of_results_per_query} """

        await __event_emitter__(
            {
                "type": "citation",
                "data": {
                    "document": [tool_tip_content],
                    "metadata": [
                        {"source": "Lookup"},
                    ],
                    "source": {
                        "name": "🔎 Lookup",
                    },
                },
            }
        )

        seen_urls = {}  # Hashmap to store seen URLs
        duplicate_results = 0
        content_citations_list = []

        for query in queries:
            search_url = f"{searxng_url}/search"
            params = {
                "q": query,
                "safesearch": int(safesearch),
                "format": "json",
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(search_url, params=params, timeout=20)
                    response.raise_for_status()
                    data = response.json()

                if "results" in data:
                    results = data["results"]
                    if not results:
                        output += f"No results found for query: {query}\n"
                        continue

                    block_quote = ""
                    result_count = 0  # for counting the result
                    for result in results[:number_of_results_per_query]:
                        url = result.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls[url] = True  # Mark URL as seen
                            title = result.get("title", "No Title")
                            content = result.get("content", "No Content")
                            if content:

                                content = content.replace("[", "&lbrack;")
                                content = content.replace("]", "&rbrack;")

                                citation_number = result_count + 1

                                block_quote += (
                                    f"> {citation_number}. [{title}]({url})\n"
                                )
                                block_quote += f"> {content}\n"
                                result_count += 1

                                await __event_emitter__(
                                    {
                                        "type": "citation",
                                        "data": {
                                            "document": [content],
                                            "metadata": [
                                                {"source": title},
                                            ],
                                            "source": {
                                                "name": f"{citation_number}. {title}",
                                                "url": url,
                                            },
                                        },
                                    }
                                )
                        else:
                            duplicate_results += 1

                    output += block_quote
                else:
                    output += f"Error: Unexpected response format from search engine for query: {query}\n"

            except httpx.TimeoutException:
                output += f"Error: Timeout connecting to SearXNG for query: {query}. Please check the URL and try again.\n"
            except httpx.RequestError as e:
                output += (
                    f"Error connecting to search engine for query: {query}: {e}.\n"
                )
            except Exception as e:
                output += f"An unexpected error occurred for query: {query}: {e}\n"

        if duplicate_results > 0:
            output += f"\n> {duplicate_results} results omitted. "

        return output
