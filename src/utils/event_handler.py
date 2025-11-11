from typing import Dict, List, Tuple


class EventProcessor:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.response_parts: List[str] = []
        self.tool_calls: List[Dict] = []

    def process_event(self, event) -> None:
        function_calls = event.get_function_calls()
        if function_calls:
            for call in function_calls:
                tool_call = {"name": call.name, "args": call.args or {}}
                self.tool_calls.append(tool_call)

                if self.verbose:
                    print(f"🔧 Tool Called: {call.name}")
                    if call.args:
                        print(f"   Args: {call.args}")

        function_responses = event.get_function_responses()
        if function_responses:
            for response in function_responses:
                if self.verbose:
                    print(f"📥 Tool Response from {response.name}:")
                    if response.response:
                        print(f"   {response.response}")

        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        self.response_parts.append(part.text)

    def get_response(self) -> str:
        return (
            "".join(self.response_parts).strip()
            if self.response_parts
            else "No response received"
        )

    def get_tool_calls(self) -> List[Dict]:
        return self.tool_calls

    def reset(self) -> None:
        self.response_parts = []
        self.tool_calls = []


async def process_runner_events(
    runner_async_generator, verbose: bool = False
) -> Tuple[str, List[Dict]]:
    processor = EventProcessor(verbose=verbose)

    async for event in runner_async_generator:
        processor.process_event(event)

    return processor.get_response(), processor.get_tool_calls()
