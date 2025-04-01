"""
title: Native tool call formatting outlet
author: Raphael
author_url: https://github.com/raphael1-w
description: Avoid confusing the model on native tool call syntax in subsequent messages by updating the <details> tag in the native tool call response.
required_open_webui_version: 0.6.0
version: 1.0.0
licence: GNU General Public License v3.0
"""

import re  # Import the regular expression module
from pydantic import BaseModel
from typing import Optional


class Filter:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # print(f"inlet called: {body}") # Keep print statements if needed for debugging
        return body

    def stream(self, event: dict) -> dict:
        # print(f"stream event: {event}") # Keep print statements if needed for debugging
        return event

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # print(f"outlet called: {body}") # Keep print statements if needed for debugging
        note = "THIS IS NOT THE SYNTAX TO USE TOOLS, REMEMBER YOUR SYSTEM PROMPT"

        # Regex to find the <details> tag and capture parts needed for modification
        # Captures:
        # Group 1: The part up to and including the name attribute (e.g., <details ... name="tool_name")
        # Group 2: The whitespace between the name attribute and the arguments attribute
        # Group 3: The arguments attribute and the rest of the tag's opening part (e.g., arguments="..." result="...">)
        pattern = re.compile(
            r'(<details\s+type="tool_calls"[^>]*?\sname="[^"]*")(\s+)(arguments="[^"]*"[^>]*?>)'
        )

        for message in body["messages"]:
            if (
                message["role"] == "assistant"
                and '<details type="tool_calls"' in message["content"]
            ):
                original_content = message["content"]

                # Define the replacement string using backreferences
                # Inserts the note_to_model attribute between group 1 and group 2/3
                replacement = rf'\1 note_to_model="{note}"\2\3'

                # Perform the substitution
                modified_content = pattern.sub(replacement, original_content)

                # Update the message content only if a change was made
                if modified_content != original_content:
                    message["content"] = modified_content
                    # print(f"Modified content: {message['content']}") # Optional: print modified content for verification

        return body
