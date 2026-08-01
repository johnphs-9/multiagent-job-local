# CrewAI and Ollama Compatibility

The supported baseline is intentionally narrow because this application depends on
structured JSON output, tool-free local inference, and enough context for JD/CV evidence.

### Recommended models to use

In general, `gemma4` is recommended for a good balance of speed and quality output.

| Profile | Default model | Approximate model download | Practical memory |
|---|---|---:|---:|
| Preview | `llama3.2:latest` | about 2 GB | 8 GB minimum |
| Demo | `gemma4:latest` | about 9.6 GB | 16 GB minimum; 24 GB recommended |
| Deep | `gemma4:26b` | about 17 GB | 32 GB minimum; 48 GB recommended |

### Model Information

| Application profile | Ollama model tag | Model info | Intended use | Status |
|---|---|---|---|---|
| Preview | `llama3.2:latest` | 3.2B; Q4_K_M; Text only, no dedicated thinking mode | Fast smoke test, 3 role + 1 HR question; best suited for lightweight chat and simple use. | Supported baseline |
| Demo | `gemma4:latest` | 8.0B; Q4_K_M; Text/Image/Audio, configurable thinking; intended for efficient local or edge deployment. | Showcase run with up to 12 questions. Recommended model. | Supported baseline |
| Demo | `qwen3.5:9b` | 9B; Q4_K_M; Dense multimodal model; Text and images | Showcase run with up to 12 questions. | Supported |
| Demo | `qwen3:14b` | 14B; Q4_K_M; Dense language model; Text only | Showcase run with up to 12 questions.  | Supported |
| Deep | `qwen3:32b` | 32B; Q4_K_M; Dense transformer model; Text only, strong for reasoning, mathematics, coding, multilingual work. | Deep analysis run with up to 26 questions.  | Supported |
| Deep | `gemma4:26b` | 25.8B; Q4_K_M; Mixture-of-Experts model; Text only, configurable thinking, strong for reasoning, coding and vision. | Larger local analysis, up to 3 review cycles | Supported baseline when hardware allows |


### CrewAI and Ollama compatibility

CrewAI is constrained by `crewai[litellm]>=1.15.5,<2` in `pyproject.toml`. Other Ollama
models may work if they support the selected context window, JSON/structured output, and
the configured token budget, but they are not compatibility-tested. Model tags are mutable;
for a repeatable showcase, record the exact Ollama model digest returned by `ollama list`
and keep the selected model in `.env`.

The Preview profile is the required compatibility smoke test. Demo and Deep are optional
because latency and memory use vary substantially by workstation.
