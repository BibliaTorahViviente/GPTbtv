import argparse
from collections import defaultdict
import datetime
import json
import os
import time

import gradio as gr
import requests

from chatserver.conversation import default_conversation
from chatserver.constants import LOGDIR
from chatserver.utils import build_logger


logger = build_logger("gradio_web_server", "gradio_web_server.log")

upvote_msg = "👍  Upvote the last response"
downvote_msg = "👎  Downvote the last response"
init_prompt = default_conversation.get_prompt()

priority = {
}

def get_conv_log_filename():
    t = datetime.datetime.now()
    name = os.path.join(LOGDIR, f"{t.year}-{t.month:02d}-{t.day:02d}-conv.json")
    return name


def get_model_list():
    ret = requests.post(args.controller_url + "/refresh_status")
    assert ret.status_code == 200
    ret = requests.post(args.controller_url + "/list_models")
    models = ret.json()["models"]
    models.sort(key=lambda x: priority.get(x, x))
    logger.info(f"Models: {models}")
    return models


def add_text(state, text, request: gr.Request):
    text = text[:1536]  # Hard cut-off
    state.append_message(state.roles[0], text)
    state.append_message(state.roles[1], None)
    return state, state.to_gradio_chatbot(), "", upvote_msg, downvote_msg


def clear_history():
    state = default_conversation.copy()
    return state, state.to_gradio_chatbot()


def regenerate(state):
    state.messages[-1][-1] = None
    return state, state.to_gradio_chatbot(), upvote_msg, downvote_msg


def load_demo(request: gr.Request):
    models = get_model_list()
    logger.info(f"load demo: {request.client.host}")
    state = default_conversation.copy()
    return (gr.Dropdown.update(
                choices=models,
                value=models[0] if len(models) > 0 else ""),
            state, state.to_gradio_chatbot())


def vote_last_response(state, vote_type, model_selector, request: gr.Request):
    logger.info(f"vote_type: {vote_type}")
    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(time.time(), 4),
            "type": vote_type,
            "model": model_selector,
            "state": state.dict(),
            "ip": request.client.host,
        }
        fout.write(json.dumps(data) + "\n")


def upvote_last_response(state, upvote_btn, downvote_btn, model_selector,
                         request: gr.Request):
    if upvote_btn == "done" or len(state.messages) == state.offset:
        return "done", "done"
    vote_last_response(state, "upvote", model_selector, request)
    return "done", "done"


def downvote_last_response(state, upvote_btn, downvote_btn, model_selector,
                           request: gr.Request):
    if upvote_btn == "done" or len(state.messages) == state.offset:
        return "done", "done"
    vote_last_response(state, "downvote", model_selector, request)
    return "done", "done"


def http_bot(state, model_selector, request: gr.Request):
    start_tstamp = time.time()

    # Query worker address
    controller_url = args.controller_url
    ret = requests.post(controller_url + "/get_worker_address",
            json={"model_name": model_selector})
    worker_addr = ret.json()["address"]
    logger.info(f"model_name: {model_selector}, worker_addr: {worker_addr}")

    # No available worker
    if worker_addr == "":
        state.messages[-1][-1] = "**NETWORK ERROR. PLEASE TRY AGAIN OR CHOOSE OTHER MODELS.**"
        yield state, state.to_gradio_chatbot()
        return

    # Construct prompt
    prompt = state.get_prompt()
    txt = prompt.replace(state.sep, '\n')
    logger.info(f"==== Conversation ====\n{txt}")

    # Make requests
    headers = {"User-Agent": "Alpa Client"}
    pload = {
        "prompt": prompt,
        "max_new_tokens": 512,
        "temperature": 0.7,
        "stop": state.sep,
    }
    response = requests.post(worker_addr + "/generate_stream",
        headers=headers, json=pload, stream=True)

    # Stream output
    for chunk in response.iter_lines(chunk_size=8192, decode_unicode=False, delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode("utf-8"))
            output = data["text"][len(prompt) + 2:]
            state.messages[-1][-1] = output
            yield state, state.to_gradio_chatbot()
    finish_tstamp = time.time()
    logger.info(f"{output}")

    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(finish_tstamp, 4),
            "type": "chat",
            "model": model_selector,
            "start": round(start_tstamp, 4),
            "finish": round(start_tstamp, 4),
            "state": state.dict(),
            "ip": request.client.host,
        }
        fout.write(json.dumps(data) + "\n")


def build_demo():
    models = get_model_list()
    css = (
        """#model_selector_row {width: 400px;}"""
        #"""#chatbot {height: 5000px;}"""
    )

    with gr.Blocks(title="Chat Server", css=css) as demo:
        gr.Markdown(
            "# Chat server\n"
            "### Terms of Use\n"
            "By using this service, users are required to agree to the following terms: The service is a research preview intended for non-commercial use only. It does not provide safety measures and may generate offensive content. It must not be used for any illegal, harmful, violent, racist, or sexual purposes. The service may collect user dialogue data for future research."
        )

        state = gr.State()

        with gr.Row(elem_id="model_selector_row"):
            model_selector = gr.Dropdown(
                choices=models,
                value=models[0] if len(models) > 0 else "",
                interactive=True,
                label="Choose a model to chat with.")

        chatbot = gr.Chatbot(elem_id="chatbot")
        textbox = gr.Textbox(show_label=False,
            placeholder="Enter text and press ENTER",).style(container=False)

        with gr.Row():
            upvote_btn = gr.Button(value=upvote_msg)
            downvote_btn = gr.Button(value=downvote_msg)
            regenerate_btn = gr.Button(value="Regenerate")
            clear_btn = gr.Button(value="Clear history")

        upvote_btn.click(upvote_last_response,
            [state, upvote_btn, downvote_btn, model_selector],
            [upvote_btn, downvote_btn])
        downvote_btn.click(downvote_last_response,
            [state, upvote_btn, downvote_btn, model_selector],
            [upvote_btn, downvote_btn])
        regenerate_btn.click(regenerate, state,
            [state, chatbot, upvote_btn, downvote_btn]).then(
            http_bot, [state, model_selector], [state, chatbot])
        clear_btn.click(clear_history, None, [state, chatbot])

        textbox.submit(add_text, [state, textbox],
            [state, chatbot, textbox, upvote_btn, downvote_btn]).then(
            http_bot, [state, model_selector], [state, chatbot])

        demo.load(load_demo, [], [model_selector, state, chatbot])

    return demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int)
    parser.add_argument("--controller-url", type=str, default="http://localhost:21001")
    parser.add_argument("--concurrency-count", type=int, default=2)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    demo = build_demo()
    demo.queue(concurrency_count=args.concurrency_count, status_update_rate=10).launch(
        server_name=args.host, server_port=args.port, share=args.share)
