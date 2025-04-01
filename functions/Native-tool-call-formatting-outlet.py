"""
title: Native tool call formatting outlet
author: Raphael
author_url: https://github.com/raphael1-w
description: Avoid confusing the model on native tool call syntax in subsequent messages by removing the <details> tag block from the native tool call response.
required_open_webui_version: 0.6.0
version: 1.1.0
licence: GNU General Public License v3.0
"""

# No longer need 're' since we are using string methods
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

        # Define the start and end tags we want to remove
        start_tag_marker = '<details type="tool_calls"'
        end_tag_marker = "</details>"

        # Ensure 'messages' key exists and is a list
        if "messages" in body and isinstance(body["messages"], list):
            for message in body["messages"]:
                # Check if the message is from the assistant and potentially contains the tool call tag
                if (
                    message["role"] == "assistant"
                    and isinstance(
                        message.get("content"), str
                    )  # Ensure content is a string
                    and start_tag_marker in message["content"]
                ):
                    original_content = message["content"]
                    modified_content = ""
                    last_index = 0

                    while True:
                        # Find the start of the next tool call block
                        start_index = original_content.find(
                            start_tag_marker, last_index
                        )

                        if start_index == -1:
                            # No more tool call blocks found, append the rest of the string
                            modified_content += original_content[last_index:]
                            break

                        # Find the end of the corresponding </details> tag
                        # Start searching *after* the beginning of the start tag marker
                        end_index = original_content.find(
                            end_tag_marker, start_index + len(start_tag_marker)
                        )

                        if end_index == -1:
                            # Malformed content: found start but no end tag.
                            # Append the rest of the string from the last safe point and stop processing this message.
                            # This prevents accidentally removing content if the tags are broken.
                            print(
                                f"Warning: Found '{start_tag_marker}' without matching '{end_tag_marker}' in message. Stopping removal for this message."
                            )
                            modified_content += original_content[last_index:]
                            break

                        # Append the content *before* the start tag
                        modified_content += original_content[last_index:start_index]

                        # Update the index to search from after the removed block
                        # The '+ len(end_tag_marker)' ensures we skip over the end tag itself
                        last_index = end_index + len(end_tag_marker)

                    # Update the message content only if a change was potentially made
                    # (Check length or content equality, equality check is safer)
                    if modified_content != original_content:
                        message["content"] = (
                            modified_content.strip()
                        )  # Use strip() to remove potential leading/trailing whitespace left after removal
                        # If the entire content was just the tool call, it might become empty
                        if not message["content"]:
                            # Decide what to do with an empty message. Options:
                            # 1. Keep it empty: message["content"] = "" (already done by strip potentially)
                            # 2. Add placeholder: message["content"] = "(Tool call details removed)"
                            # 3. Potentially remove the message entirely (more complex, might break conversation flow)
                            # Let's stick with potentially empty for now.
                            pass
                        # print(f"Modified content: {message['content']}") # Optional: print modified content for verification
        else:
            # Handle cases where 'messages' might be missing or not a list
            print("Warning: 'messages' key not found or not a list in the body.")

        return body
