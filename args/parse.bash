#!/bin/bash

export GGML_CUDA_ENABLE_UNIFIED_MEMORY=ON

~/llm/llama.cpp/build/bin/llama-server \
    --host localhost \
    --port 9931 \
    --hf-repo unsloth/Qwen3.8-27B-GGUF:Q8_K_XL \
    --spec-type draft-mtp \
    --spec-draft-n-max 3 \
    --ctx-size 262144 \
    --image-min-tokens 1024 \
    --parallel 4 \
    --temp 0.7 \
    --top-k 20 \
    --min-p 0.0 \
    --presence-penalty 1.5 \
    --repeat-penalty 1.0 \
    --chat-template-kwargs '{"enable_thinking":false}'


    # --models-preset preset.ini \
    # --hf-repo unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL


