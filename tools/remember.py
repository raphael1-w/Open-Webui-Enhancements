"""
title: Remember
author: Raphael Wong
author_url: https://github.com/raphael1-w
description: This tool allows the LLM to update the user's memory list, including adding new memories and consolidating existing ones.
required_open_webui_version: 0.5.0
version: 0.5.0
licence: GNU General Public License v3.0
"""

from typing import List, Literal, Optional, Callable, Any
from pydantic import BaseModel, Field
from open_webui.models.memories import Memories
from datetime import datetime


class Tools:
    def __init__(self):
        self.citation = False  # Disable built-in citations
        self.valves = self.Valves()

    class Valves(BaseModel):
        include_memory_list: bool = Field(
            default=False,
            description="Whether to include the updated memory bank in the return message.",
        )

    async def add_memory(
        self,
        content: str,
        __user__: dict,
        __event_emitter__=None,
    ) -> str:
        """
        Add a new memory to the user's memory bank. Before you use this tool, first check for related memories. If a related memory exists, you should update that memory with the new information instead of adding a new memory.
        """
        user_id = __user__.get("id")
        if not user_id:
            return "Error: User ID not provided."
        new_memory = Memories.insert_new_memory(user_id, content)

        if new_memory:
            content_list = []
            # Fetch updated memories after addition
            user_memories = Memories.get_memories_by_user_id(user_id)

            if user_memories:
                content_string = "\n".join(
                    [
                        f"{index}. {memory.content}"
                        for index, memory in enumerate(
                            sorted(user_memories, key=lambda m: m.created_at), start=1
                        )
                    ]
                )

            await __event_emitter__(
                {
                    "type": "citation",
                    "data": {
                        "document": [
                            f"Added new memory - {content} \n---\nUpdated memory bank: \n{content_string}"
                        ],
                        "metadata": [
                            {"source": "Remember"},
                        ],
                        "source": {
                            "name": "🧠 Remember",
                        },
                    },
                }
            )

            if self.valves.include_memory_list:
                return f"Added new memory - {content} \nUpdated memory bank: \n{content_string}"
            else:
                return f"Success"
        else:
            return "Failed to add new memory."

    async def update_memory(
        self,
        new_content: str,
        old_content: str,
        __user__: dict,
        __event_emitter__=None,
    ) -> str:
        """
        Update an existing memory by finding a memory that matches the 'old_content' text
        and replacing its content with 'new_content'. If multiple memories match
        'old_content', only the first one found will be updated.
        """
        user_id = __user__.get("id")
        if not user_id:
            return "Error: User ID not provided."

        # Fetch all memories for the user
        user_memories = Memories.get_memories_by_user_id(user_id)
        if not user_memories:
            return "No memories found for this user."

        # Find the memory to update by matching content
        memory_to_update = None
        memory_id_to_delete = None
        for memory in user_memories:
            if memory.content == old_content:
                memory_to_update = memory
                memory_id_to_delete = (
                    memory.id
                )  # Assuming memory object has an 'id' attribute
                break  # Stop after finding the first match

        if not memory_to_update:
            return f"Error: Memory with content '{old_content}' not found."

        # Delete the old memory using its ID
        delete_old_memory = Memories.delete_memory_by_id(memory_id_to_delete)

        # Insert the new memory
        insert_new_memory_success = False
        if delete_old_memory:
            # Only insert the new one if the old one was successfully deleted
            new_memory_obj = Memories.insert_new_memory(user_id, new_content)
            if new_memory_obj:
                insert_new_memory_success = True

        if delete_old_memory and insert_new_memory_success:
            # Fetch updated memories to display (optional)
            updated_user_memories = Memories.get_memories_by_user_id(user_id)
            content_string = ""
            if updated_user_memories:
                content_string = "\n".join(
                    [
                        f"{index}. {memory.content}"
                        for index, memory in enumerate(
                            sorted(updated_user_memories, key=lambda m: m.created_at),
                            start=1,  # Assuming 'created_at' attribute
                        )
                    ]
                )

            # Emit event (optional)
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "citation",
                        "data": {
                            "document": [
                                f"Updated memory: Replaced '{old_content}' with '{new_content}'.\n---\nUpdated memory bank: \n{content_string}"
                            ],
                            "metadata": [{"source": "Remember"}],
                            "source": {"name": "🧠 Remember"},
                        },
                    }
                )

            # Return result
            if self.valves.include_memory_list:
                return f"Updated memory: Replaced '{old_content}' with '{new_content}'.\nUpdated memory bank: \n{content_string}"
            else:
                return "Successfully updated memory."
        elif not delete_old_memory:
            # Handle case where deletion failed (e.g., ID was wrong, DB error)
            # Maybe try to re-insert the original memory? Or just report error.
            # For now, just report a generic failure.
            return f"Failed to update memory. Could not delete the old memory with content: '{old_content}'."
        else:
            # Handle case where insertion failed after deletion
            # This leaves the memory deleted but not replaced. Maybe try rollback?
            # For now, report the specific failure.
            return f"Failed to update memory. Deleted old memory '{old_content}', but failed to add new memory '{new_content}'."

    async def forget_memory(
        self,
        memory_id: str,
        __user__: dict,
        __event_emitter__=None,
    ) -> str:
        """
        Delete a memory from the user's memory bank.
        """
        user_id = __user__.get("id")
        if not user_id:
            return "Error: User ID not provided."

        # Get the memory content before deleting
        memory_to_delete = Memories.get_memory_by_id(memory_id)
        if not memory_to_delete:
            return "Memory not found."
        memory_content = memory_to_delete.content

        # Delete memory
        delete_memory = Memories.delete_memory_by_id(memory_id)
        if delete_memory:
            content_list = []
            # Fetch updated memories after deletion
            user_memories = Memories.get_memories_by_user_id(user_id)
            if user_memories:
                content_string = "\n".join(
                    [
                        f"{index}. {memory.content}"
                        for index, memory in enumerate(
                            sorted(user_memories, key=lambda m: m.created_at), start=1
                        )
                    ]
                )

            await __event_emitter__(
                {
                    "type": "citation",
                    "data": {
                        "document": [
                            f"Deleted memory - {memory_content}\n---\nUpdated memory bank: \n{content_string}"
                        ],
                        "metadata": [
                            {"source": "Remember"},
                        ],
                        "source": {
                            "name": "🧠 Remember",
                        },
                    },
                }
            )
            if self.valves.include_memory_list:
                return f"Deleted memory - {memory_content}\nUpdated memory bank: \n{content_string}"
            else:
                return f"Success"
        else:
            return "Failed to delete memory."
