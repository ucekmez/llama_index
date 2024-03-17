import llama_index.core.instrumentation as instrument
from llama_index.core.instrumentation.span_handlers import SimpleSpanHandler
from llama_index.core.llama_dataset.simple import LabelledSimpleDataset
from llama_index.packs.diff_private_simple_dataset.base import PromptBundle
from llama_index.packs.diff_private_simple_dataset import DiffPrivateSimpleDatasetPack
from llama_index.llms.openai import OpenAI
import tiktoken
from .event_handler import DiffPrivacyEventHandler
import asyncio
import os


event_handler = DiffPrivacyEventHandler()
span_handler = SimpleSpanHandler()
dispatcher = instrument.get_dispatcher()
dispatcher.add_span_handler(span_handler)
dispatcher.add_event_handler(event_handler)


async def main():
    # load simple dataset
    json_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "symptom_2_disease.json"
    )
    simple_dataset = LabelledSimpleDataset.from_json(json_path)

    # init pack
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        max_tokens=1,
        logprobs=True,
        top_logprobs=5,
    )
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo-instruct")

    prompt_bundle = PromptBundle(
        instruction=(
            "Given a label of disease type, generate the chosen type of symptoms accordingly.\n"
            "Start your answer directly after 'Symptoms: '. Begin your answer with [RESULT].\n"
        ),
        label_heading="Disease",
        text_heading="Symptoms",
    )

    dp_simple_dataset_pack = DiffPrivateSimpleDatasetPack(
        llm=llm,
        tokenizer=tokenizer,
        prompt_bundle=prompt_bundle,
        simple_dataset=simple_dataset,
        sephamore_counter_size=2,
        sleep_time_in_seconds=0.3,
    )

    synthetic_dataset = await dp_simple_dataset_pack.arun(
        sizes=4,
        t_max=150,
        sigma=0.5,
        num_splits=3,
        num_samples_per_split=8,
    )


if __name__ == "__main__":
    if os.environ.get("OPENAI_API_KEY") is None:
        raise ValueError(
            "Missing OPENAI_API_KEY. Please run `export OPENAI_API_KEY=...`"
        )
    asyncio.run(main())
