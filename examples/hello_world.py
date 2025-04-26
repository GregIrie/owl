from owl.node import BaseNode, InputNode
from owl.node import LlmNode  # si besoin
from owl.core_type import NodeInputType
from typing import Dict, Any

def translate_to_fr(text: Dict[str,Any]):
    #print(text)
    return({'translated':"Bonjour le monde"})

def translate_to_en(text):
    return({'translated':"Hello world"})

def count_words(translated: str) -> Dict[str,int]:
    return { 'count': len(translated.split()) }

# 1. Déclarer vos prototypes une fois
word_count = BaseNode(
    name='word_count',
    input_types=NodeInputType(required={'translated': str}),
    output_types=NodeInputType(required={'count': int}),
    run_fn=count_words
)

print(f'-------------------------- {word_count.input_types.keys()}')

fr_translate = BaseNode(
    name='fr_translate',
    input_types=NodeInputType(required={'text': str}),
    output_types=NodeInputType(required={'translated': str}),
    run_fn=translate_to_fr
)

en_translate = BaseNode(
    name='en_translate',
    input_types=NodeInputType(required={'text': str}),
    output_types=NodeInputType(required={'translated': str}),
    run_fn=translate_to_en
)

# 2. Construire le graphe dans un contexte
from owl.workflow import Workflow

if __name__ == "__main__":
    with Workflow('translate_and_count') as wf:
        inp = InputNode('initial_input', input_types = NodeInputType(required={'text': str}), output_types=NodeInputType(required={'text': str}))()
        wc_fr = word_count(fr_translate(inp), alias='word_count_fr')
        wc_en = word_count(en_translate(inp), alias='word_count_en')
    # execute the workflow with an example input
    #print(inp)
    results = wf.run({'text': 'hello world'})
    print("Workflow results:", results)
    print("type results:", type(results))

# `wf` contient maintenant un DAG identique à :
#   inp -> fr_translate -> wc_fr
#   inp -> en_translate -> wc_en