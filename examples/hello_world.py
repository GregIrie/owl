from owl.decorator import node
from owl.types     import NodeInputType
from owl.decorator import workflow
from owl.workflow  import Workflow
from owl.decorator import get_registered_nodes





@node(
    name="translate_text",
    input_types=NodeInputType(required={"text": str}),
    output_types=NodeInputType(required={"translation": str}),
    #provider="openai",           # LLM-powered node
    #model_name="gpt-4",
    )
def translate_text(text: str) -> dict:
    # (LLM call handled under the hood;
    # this stub only defines types & provider)
    return {"translation":"Hello world"}


@node(
    name="count_words",
    input_types=NodeInputType(required={"translation": str}),
    output_types=NodeInputType(required={"word_count": int}),
    )
def count_words(translation) -> dict:
    return {"word_count": len(translation.split())}



@workflow("text_processing_pipeline")
def build_wf(wf: Workflow):
    # Fetch declared nodes
    translate = get_registered_nodes()["translate_text"]
    count     = get_registered_nodes()["count_words"]

    # Assemble DAG
    wf.add_node(translate) \
      .add_node(count) \
      .connect(translate, count)
    return wf
    
if __name__ == "__main__":
    wf = build_wf()
    wf.pretty_print()
    results = wf.run({"text": "Bonjour le monde!"})
    print(results)
    # ➞ {"text": "Bonjour le monde!", "translation": "...", "word_count": 3}