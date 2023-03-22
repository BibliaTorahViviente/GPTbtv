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


def add_text(history, text, request: gr.Request):
    # Fix some bugs in gradio UI
    for i in range(len(history)):
        history[i][0] = history[i][0].replace("<br>", "")
        if history[i][1]:
            history[i][1] = history[i][1].replace("<br>", "")
    history = history + [[text, None]]
    return history, "", upvote_msg, downvote_msg


def clear_history(history):
    return []


def load_demo(request: gr.Request):
    models = get_model_list()
    logger.info(f"load demo: {request.client.host}")
    return gr.Dropdown.update(
        choices=models,
        value=models[0] if len(models) > 0 else "")


def vote_last_response(history, vote_type, model_selector, request: gr.Request):
    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(time.time(), 4),
            "type": vote_type,
            "model": model_selector,
            "conversation": history,
            "init_prompt": init_prompt,
            "ip": request.client.host,
        }
        fout.write(json.dumps(data) + "\n")


def upvote_last_response(history, upvote_btn, downvote_btn, model_selector,
                         request: gr.Request):
    if upvote_btn == "done" or len(history) == 0:
        return "done", "done"
    vote_last_response(history, "upvote", model_selector, request)
    return "done", "done"


def downvote_last_response(history, upvote_btn, downvote_btn, model_selector,
                           request: gr.Request):
    if upvote_btn == "done" or len(history) == 0:
        return "done", "done"
    vote_last_response(history, "downvote", model_selector, request)
    return "done", "done"


def http_bot(history, model_selector, request: gr.Request):
    start_tstamp = time.time()
    controller_url = args.controller_url
    ret = requests.post(controller_url + "/get_worker_address",
            json={"model_name": model_selector})
    worker_addr = ret.json()["address"]
    logger.info(f"model_name: {model_selector}, worker_addr: {worker_addr}")

    # Fix some bugs in gradio UI
    for i in range(len(history)):
        history[i][0] = history[i][0].replace("<br>", "")
        if history[i][1]:
            history[i][1] = history[i][1].replace("<br>", "")

    # No available worker
    if worker_addr == "":
        history[-1][-1] = "**NETWORK ERROR. PLEASE TRY AGAIN OR CHOOSE OTHER MODELS.**"
        yield history
        return

    # Construct prompt
    conv = default_conversation.copy()
    conv.append_gradio_chatbot_history(history)
    prompt = conv.get_prompt()
    txt = prompt.replace(conv.sep, '\n')
    logger.info(f"==== Conversation ====\n{txt}")

    # Make requests
    headers = {"User-Agent": "Alpa Client"}
    pload = {
        "prompt": prompt,
        "max_new_tokens": 512,
        "temperature": 0.7,
        "stop": conv.sep,
    }
    response = requests.post(worker_addr + "/generate_stream",
        headers=headers, json=pload, stream=True)

    # Stream output
    sep = f"{conv.sep}{conv.roles[1]}: "
    for chunk in response.iter_lines(chunk_size=8192, decode_unicode=False, delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode("utf-8"))
            output = data["text"].split(sep)[-1]
            history[-1][-1] = output
            yield history
    logger.info(f"{output}")
    finish_tstamp = time.time()

    with open(get_conv_log_filename(), "a") as fout:
        data = {
            "tstamp": round(finish_tstamp, 4),
            "type": "chat",
            "model": model_selector,
            "start": round(start_tstamp, 4),
            "finish": round(start_tstamp, 4),
            "conversation": history,
            "init_prompt": init_prompt,
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
            "By using this service, users are required to agree to the following terms: The service is a research preview intended for non-commercial use only. It does not provide safety measures and may generate offensive content. It must not be used for any illegal, harmful, violent, racist, or sexual purposes. The service collects user dialogue data for future research."
        )

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
            clear_btn = gr.Button(value="Clear history")

        upvote_btn.click(upvote_last_response,
            [chatbot, upvote_btn, downvote_btn, model_selector],
            [upvote_btn, downvote_btn])
        downvote_btn.click(downvote_last_response,
            [chatbot, upvote_btn, downvote_btn, model_selector],
            [upvote_btn, downvote_btn])
        clear_btn.click(clear_history, chatbot, chatbot)

        textbox.submit(add_text, [chatbot, textbox],
            [chatbot, textbox, upvote_btn, downvote_btn]).then(
            http_bot, [chatbot, model_selector], chatbot,
        )

        demo.load(load_demo, [], model_selector)

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
