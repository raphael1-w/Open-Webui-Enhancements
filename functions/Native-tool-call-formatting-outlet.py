"""
title: Native tool call formatting outlet
author: Raphael
author_url: https://github.com/raphael1-w
description: Avoid confusing the model on native tool call syntax in subsequent messages by altering the <details> tag block from the native tool call response.
required_open_webui_version: 0.6.0
version: 1.1.0
licence: GNU General Public License v3.0
"""

import re
from pydantic import BaseModel
from typing import Optional


class Filter:
    class Valves(BaseModel):
        pass  # Define valves if needed, otherwise pass

    def __init__(self):
        self.valves = self.Valves()
        # print("Filter initialized") # Optional: for debugging

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # print(f"inlet called: {body}") # Optional: for debugging
        return body

    def stream(self, event: dict) -> dict:
        # print(f"stream event: {event}") # Optional: for debugging
        return event

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # print(f"outlet called: {body}") # Keep print statements if needed for debugging

        # Define the start and end tags we want to find
        start_tag_marker = '<details type="tool_calls"'
        end_tag_marker = "</details>"

        # Regular expression to find the name attribute within the start tag
        # It looks for name="<something>" and captures <something>
        name_regex = re.compile(r'name="([^"]+)"')

        # Ensure 'messages' key exists and is a list
        if "messages" in body and isinstance(body["messages"], list):
            for message in body["messages"]:
                # Check if the message is from the assistant and potentially contains the tool call tag
                if (
                    message["role"] == "assistant"
                    and isinstance(message.get("content"), str)
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
                        end_index = original_content.find(
                            end_tag_marker, start_index + len(start_tag_marker)
                        )
                        if end_index == -1:
                            # Malformed content: found start but no end tag.
                            print(
                                f"Warning: Found '{start_tag_marker}' without matching '{end_tag_marker}' in message. Stopping replacement for this message."
                            )
                            # Append the rest from the last safe point to avoid data loss
                            modified_content += original_content[last_index:]
                            break

                        # ---- Modification Start ----

                        # Extract the opening tag itself to search for the name attribute
                        # Find the closing '>' of the opening <details> tag
                        tag_end_index = original_content.find(">", start_index)
                        if tag_end_index == -1 or tag_end_index > end_index:
                            # Malformed tag or '>' appears after '</details>'? Skip this block safely.
                            print(
                                f"Warning: Could not find closing '>' for the tag starting at {start_index}. Skipping block."
                            )
                            modified_content += original_content[
                                last_index : end_index + len(end_tag_marker)
                            ]  # Add the original block back
                            last_index = end_index + len(end_tag_marker)
                            continue  # Move to the next potential block

                        opening_tag = original_content[start_index : tag_end_index + 1]

                        # Search for the name attribute within the opening tag
                        match = name_regex.search(opening_tag)
                        tool_name = (
                            "unknown_tool"  # Default if name attribute not found
                        )
                        if match:
                            tool_name = match.group(
                                1
                            )  # Get the captured group (the tool name)

                        # Construct the replacement string
                        replacement_string = f"\n↳ **Used `{tool_name}` tool**\n"

                        # Append the content _before_ the start tag
                        modified_content += original_content[last_index:start_index]

                        # Append the replacement string instead of the original block
                        modified_content += replacement_string

                        # Update the index to search from after the removed block
                        last_index = end_index + len(end_tag_marker)

                        # ---- Modification End ----

                    # Update the message content only if a change was potentially made
                    if modified_content != original_content:
                        # Strip leading/trailing whitespace from the *entire* modified content,
                        # but the newlines within the replacement string will remain.
                        message["content"] = modified_content.strip()

                        # Handle case where the content might become effectively empty
                        # (e.g., if the original message ONLY contained the tool call block)
                        if not message["content"]:
                            # Decide what to do. Let's keep it empty for now.
                            pass
                        # print(f"Modified content: {message['content']}") # Optional verification

        else:
            # Handle cases where 'messages' might be missing or not a list
            print("Warning: 'messages' key not found or not a list in the body.")

        return body
