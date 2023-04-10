"""
Chat with a model with command line interface.

Usage:
python3 -m fastchat.serve.cli --model ~/model_weights/llama-7b
"""
import argparse
import io
import re
import unicodedata

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from fastchat.serve.inference import chat_loop, ChatIO


def stream_text(output_stream, skip_echo_len: int):
    # Assuming the stream is utf-8 encoded.
    pos = 0
    # Currently, the output is the same string that keeps extending,
    # without modifying the previous part.
    for output in output_stream:
        # first, wait until the output is longer than the skip length
        if len(output) <= skip_echo_len:
            continue
        # skip the echo part
        pos = max(pos, skip_echo_len)
        new_text = output[pos:]
        if new_text:
            category = unicodedata.category(new_text[-1])
            # Check if character is a nonspacing mark
            #  (e.g., part of a multi-codepoint character)
            if category == 'Mn':
                pos = len(output) - 1
                yield new_text[:-1]
            else:
                pos = len(output)
                yield new_text

    # yield the rest of the output
    if pos < len(output):
        yield output[pos:]


class SimpleChatIO(ChatIO):
    def prompt_for_input(self, role) -> str:
        return input(f"{role}: ")

    def prompt_for_output(self, role: str):
        print(f"{role}: ", end="", flush=True)

    def stream_output(self, output_stream, skip_echo_len: int):
        # Create a StringIO object
        string_buffer = io.StringIO()
        for output in stream_text(output_stream, skip_echo_len):
            string_buffer.write(output)
            print(output, end="", flush=True)
        value = string_buffer.getvalue()
        string_buffer.close()
        return value


class RichChatIO(ChatIO):
    def __init__(self):
        self._prompt_session = PromptSession(history=InMemoryHistory())
        self._completer = WordCompleter(words=['!exit', '!reset'], pattern=re.compile('$'))
        self._console = Console()

    def prompt_for_input(self, role) -> str:
        self._console.print(f"[bold]{role}:")
        # TODO(suquark): multiline input has some issues. fix it later.
        prompt_input = self._prompt_session.prompt(
            completer=self._completer,
            multiline=False,
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=None)
        self._console.print()
        return prompt_input

    def prompt_for_output(self, role: str):
        self._console.print(f"[bold]{role}:")

    def stream_output(self, output_stream, skip_echo_len: int):
        """Stream output from a role."""
        pre = 0
        # TODO(suquark): the console flickers when there is a code block
        #  above it. We need to cut off "live" when a code block is done.

        # Create a Live context for updating the console output
        with Live(console=self._console, refresh_per_second=4) as live:
            accumulated_text = ""
            # Read lines from the stream
            for outputs in output_stream:
                outputs = outputs[skip_echo_len:].strip()
                outputs = outputs.split(" ")
                now = len(outputs) - 1
                if now > pre:
                    accumulated_text += " ".join(outputs[pre:now]) + " "
                    pre = now
                # Render the accumulated text as Markdown
                markdown = Markdown(accumulated_text)
                
                # Update the Live console output
                live.update(markdown)

            accumulated_text += " ".join(outputs[pre:])
            markdown = Markdown(accumulated_text)
            live.update(markdown)

        self._console.print()
        return outputs


def main(args):
    if args.style == "simple":
        chatio = SimpleChatIO()
    elif args.style == "rich":
        chatio = RichChatIO()
    else:
        raise ValueError(f"Invalid style for console: {args.style}")
    try:
        chat_loop(args.model_name, args.device, args.num_gpus, args.load_8bit,
                args.conv_template, args.temperature, args.max_new_tokens,
                chatio, args.debug)
    except KeyboardInterrupt:
        print("exit...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", type=str, default="facebook/opt-350m")
    parser.add_argument("--device", type=str, choices=["cpu", "cuda", "mps"], default="cuda")
    parser.add_argument("--num-gpus", type=str, default="1")
    parser.add_argument("--load-8bit", action="store_true",
        help="Use 8-bit quantization.")
    parser.add_argument("--conv-template", type=str, default="v1",
        help="Conversation prompt template.")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--style", type=str, default="simple",
                        choices=["simple", "rich"], help="Display style.")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main(args)
