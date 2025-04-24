# Orchestration Workflow for LLM (OWL)

A lightweight, Python-native DAG orchestrator built specifically for chaining Large Language Model (LLM) calls, with first-class support for type-safe node definitions, dynamic workflows, and built-in validation and logging.

---

## 🚀 Features

- **Python-first, decorator-driven API**  
  - Declare nodes with `@node(...)` (pure-Python functions or LLM-powered)  
  - Assemble workflows with `@workflow("my_workflow")` and intuitive `.add_node()` & `.connect()` calls  

- **Type-safe inputs and outputs**  
  - Define required and optional inputs/outputs via `NodeInputType`  
  - Automatic validation on execution, with clear error messages  

- **Automatic DAG management**  
  - Topological sort ensures correct execution order  
  - Cycle detection and orphan-node checks at workflow build time  
  - Visualize structure via `.pretty_print()`  

- **LLM provider integration**  
  - Plug in OpenAI, Google, Anthropic, or any custom LLM provider  
  - Switch between Python logic and LLM calls seamlessly  

- **Structured logging & error handling**  
  - Centralized `OrchestratorLogger` with console + rotating file handlers  
  - Distinct error classes: `NodeConnectionError`, `NodeValidationError`, `NodeExecutionError`  

- **Safe code execution**  
  - Sandbox arbitrary Python snippets with `interpreter.py` (timeout, limited built-ins)  

---

## 📦 Installation

```bash
git clone https://github.com/your-org/owl.git
cd owl
pip install -e .

Requirements:
	•	Python 3.8+
	•	openai, google-cloud, or other LLM SDKs (as needed)
	•	Standard logging, typing, AST, threading 
```

🎯 Quickstart

1. Declare your nodes

```python
from owl.decorator import node
from owl.types     import NodeInputType

@node(
    name="translate_text",
    input_types=NodeInputType(required={"text": str}),
    output_types=NodeInputType(required={"translation": str}),
    provider="openai",           # LLM-powered node
    model_name="gpt-4"
)
def translate_text(text: str) -> dict:
    # (LLM call handled under the hood;
    # this stub only defines types & provider)
    pass

@node(
    name="count_words",
    input_types=NodeInputType(required={"text": str}),
    output_types=NodeInputType(required={"word_count": int})
)
def count_words(text: str) -> dict:
    return {"word_count": len(text.split())}
```

2. Build your workflow
```python
from owl.decorator import workflow
from owl.workflow  import Workflow
from owl.decorator import get_registered_nodes

@workflow("text_processing_pipeline")
def build_wf(wf: Workflow):
    # Fetch declared nodes
    translate = get_registered_nodes()["translate_text"]
    count     = get_registered_nodes()["count_words"]

    # Assemble DAG
    wf.add_node(translate) \
      .add_node(count) \
      .connect(translate, count)
```
3. Run it!
```python
if __name__ == "__main__":
    wf = build_wf()
    results = wf.run({"text": "Bonjour le monde!"})
    print(results)
    # ➞ {"text": "Bonjour le monde!", "translation": "...", "word_count": 3}
```

## 📚 API Reference

**@node(...) decorator**
**Parameters:**
	•	name (str): Unique node identifier
	•	input_types (NodeInputType): Required/optional input schema
	•	output_types (NodeInputType): Output schema
	•	provider (Optional[str]): LLM provider key
	•	model_name (Optional[str])
	•	Returns:
	•	A BaseNode instance, registered for use in workflows

**@workflow(name) decorator**
**Parameters:**
	•	name (str): Workflow identifier
	•	Usage:
	•	The decorated function receives a Workflow instance (wf)
	•	Call wf.add_node(node) and wf.connect(src, dst)
	•	On decoration, cycles and orphan nodes are validated

## Core Classes

| Class      | Responsibility  |
|------------|------------|
| BaseNode | Encapsulates execution logic, type validation, LLM integration |
| Workflow | Manages nodes, connections, sorts & runs the DAG, logs progress |
| NodeInputType | Defines/validates required & optional inputs or outputs | 
| OrchestratorLogger | Provides structured console & file logging |

## 🛠️ Extending OWL
	1.	Custom Providers
Implement your own API client in owl.api_clients and refer to it via provider="your_key".
	2.	Dynamic Code Nodes
Use the interpreter module to sandbox and run ad-hoc Python/DSL snippets as nodes.
	3.	Advanced Validation
Leverage NodeInputType.add_input() / .remove_input() at runtime for dynamic schemas.

⸻

📝 License

MIT © 2025 Your Name / Your Organization