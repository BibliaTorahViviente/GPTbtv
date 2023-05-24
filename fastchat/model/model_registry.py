"""Additional information of the models."""
from collections import namedtuple
from typing import List


ModelInfo = namedtuple("ModelInfo", ["simple_name", "link", "description"])


model_info = {}


def register_model_info(
    full_names: List[str], simple_name: str, link: str, description: str
):
    info = ModelInfo(simple_name, link, description)

    for full_name in full_names:
        model_info[full_name] = info


def get_model_info(name: str) -> ModelInfo:
    return model_info[name]


register_model_info(
    ["gpt-4"], "ChatGPT-4", "https://openai.com/research/gpt-4", "ChatGPT-4 by OpenAI"
)
register_model_info(
    ["gpt-3.5-turbo"],
    "ChatGPT-3.5",
    "https://openai.com/blog/chatgpt",
    "ChatGPT-3.5 by OpenAI",
)
register_model_info(
    ["claude-v1"],
    "Claude",
    "https://www.anthropic.com/index/introducing-claude",
    "Claude by Anthropic",
)
register_model_info(
    ["claude-instant-v1"],
    "Claude Instant",
    "https://www.anthropic.com/index/introducing-claude",
    "Claude Instant by Anthropic",
)
register_model_info(
    ["bard"],
    "PaLM 2 Chat",
    "https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview#palm-api",
    "PaLM 2 for Chat by Google",
)
register_model_info(
    ["vicuna-13b", "vicuna-7b"],
    "Vicuna",
    "https://lmsys.org/blog/2023-03-30-vicuna/",
    "a chat assistant fine-tuned from LLaMA on user-shared conversations by LMSYS",
)
register_model_info(
    ["koala-13b"],
    "Koala",
    "https://bair.berkeley.edu/blog/2023/04/03/koala",
    "a dialogue model for academic research by BAIR",
)
register_model_info(
    ["oasst-pythia-12b"],
    "OpenAssistant (oasst)",
    "https://open-assistant.io",
    "an Open Assistant for everyone by LAION",
)
register_model_info(
    ["RWKV-4-Raven-14B"],
    "RMKV-4-Raven",
    "https://huggingface.co/BlinkDL/rwkv-4-raven",
    "an RNN with transformer-level LLM performance",
)
register_model_info(
    ["alpaca-13b"],
    "Alpaca",
    "https://crfm.stanford.edu/2023/03/13/alpaca.html",
    "a model fine-tuned from LLaMA on instruction-following demonstrations by Stanford",
)
register_model_info(
    ["chatglm-6b"],
    "ChatGLM",
    "https://chatglm.cn/blog",
    "an open bilingual dialogue language model by Tsinghua University",
)
register_model_info(
    ["llama-13b"],
    "LLaMA",
    "https://arxiv.org/abs/2302.13971",
    "open and efficient foundation language models by Meta",
)
register_model_info(
    ["dolly-v2-12b"],
    "Dolly",
    "https://www.databricks.com/blog/2023/04/12/dolly-first-open-commercially-viable-instruction-tuned-llm",
    "an instruction-tuned open large language model by Databricks",
)
register_model_info(
    ["stablelm-tuned-alpha-7b"],
    "StableLM",
    "https://github.com/stability-AI/stableLM",
    "Stability AI language models",
)
register_model_info(
    ["fastchat-t5-3b"],
    "FastChat-T5",
    "https://huggingface.co/lmsys/fastchat-t5-3b-v1.0",
    "a chat assistant fine-tuned from FLAN-T5 by LMSYS",
)
register_model_info(
    ["phoenix-inst-chat-7b"],
    "Phoenix-7B",
    "https://huggingface.co/FreedomIntelligence/phoenix-inst-chat-7b",
    "a multilingual chat assistant fine-tuned from Bloomz to democratize ChatGPT across languages by CUHK(SZ)",
)
register_model_info(
    ["mpt-7b-chat"],
    "MPT-Chat",
    "https://www.mosaicml.com/blog/mpt-7b",
    "a chatbot fine-tuned from MPT-7B by MosaicML",
)
register_model_info(
    ["billa-7b-sft"],
    "BiLLa-7B-SFT",
    "https://huggingface.co/Neutralzz/BiLLa-7B-SFT",
    "an instruction-tuned bilingual LLaMA with enhanced reasoning ability by an independent researcher",
)
register_model_info(
    ["h2ogpt-gm-oasst1-en-2048-open-llama-7b-preview-300bt-v2"],
    "h2oGPT-GM-7b",
    "https://huggingface.co/h2oai/h2ogpt-gm-oasst1-en-2048-open-llama-7b-preview-300bt-v2",
    "an instruction-tuned OpenLLaMA with enhanced conversational ability by H2O.ai",
)
register_model_info(
    ["baize-v2-7b", "baize-v2-13b"],
    "Baize v2",
    "https://github.com/project-baize/baize-chatbot#v2",
    "A chatbot fine-tuned from LLaMA with ChatGPT self-chat data and Self-Disillation with Feedback (SDF) by UCSD and SYSU.",
)
