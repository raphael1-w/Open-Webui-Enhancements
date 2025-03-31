"""
title: Reasoning Event Emitter Filter
author: Raphael Wong
author_url: https://github.com/raphael1-w
description: Emits a "Thinking..." event on inlet, then updates it with the elapsed time (in sec or min/sec) when the first stream chunk arrives.
required_open_webui_version: 0.5.17
version: 1.0.0
licence: GNU General Public License v3.0
"""

import time
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field


# Helper function to format duration
def format_duration(seconds: float) -> str:
    seconds = round(seconds)  # Round to nearest whole second for cleaner display
    if seconds < 60:
        return f"{seconds} second" if seconds == 1 else f"{seconds} seconds"
    else:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        minute_str = f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
        second_str = (
            f"{remaining_seconds} second"
            if remaining_seconds == 1
            else f"{remaining_seconds} seconds"
        )
        # Only include seconds if they are non-zero or if minutes are zero (shouldn't happen with < 60 check but safe)
        if remaining_seconds > 0:
            return f"{minute_str} {second_str}"
        else:
            return minute_str


class EventEmitter:
    def __init__(self, event_emitter: Optional[Callable[[dict], Any]] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown state", status="in_progress", done=True):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "status": status,
                        "done": done,
                    },
                }
            )


class Filter:
    class Valves(BaseModel):
        REASONING_TEXT: str = Field(
            default="Thinking...",
            description="Initial text to display while waiting for the model.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.start_time: Optional[float] = None
        self.first_chunk_received: bool = False

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
        __user__: Optional[dict] = None,
    ) -> dict:
        print(f"inlet called: {body}")
        self.start_time = time.time()
        self.first_chunk_received = False
        emitter = EventEmitter(__event_emitter__)
        if __event_emitter__:
            print(f"Emitting initial status: {self.valves.REASONING_TEXT}")
            await emitter.emit(
                description=self.valves.REASONING_TEXT,
                status="in_progress",
                done=False,
            )
        else:
            print("Event emitter not provided in inlet.")
        return body

    async def stream(
        self,
        event: dict,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
        __user__: Optional[dict] = None,
    ) -> dict:
        if self.start_time is not None and not self.first_chunk_received:
            end_time = time.time()
            duration_seconds = end_time - self.start_time
            self.first_chunk_received = True

            # Format the duration using the helper function
            formatted_duration = format_duration(duration_seconds)

            # Construct the final message
            final_message = f"Thought for {formatted_duration}"

            emitter = EventEmitter(__event_emitter__)
            if __event_emitter__:
                print(f"Emitting thinking time status: {final_message}")
                await emitter.emit(
                    description=final_message,
                    status="completed",
                    done=True,
                )
            else:
                print("Event emitter not provided in stream for time update.")

        return event

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        self.start_time = None
        self.first_chunk_received = False
        # print(f"outlet called: {body}") # Optional: keep for debugging
        return body
