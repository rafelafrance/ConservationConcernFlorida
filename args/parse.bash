#!/bin/bash

export GGML_CUDA_ENABLE_UNIFIED_MEMORY=ON

# model_dir=~/llm/models/unsloth/Qwen3.8-27B-GGUF
model_dir=~/llm/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF

~/llm/llama.cpp/build/bin/llama-server \
    --host localhost \
    --port 9931 \
    --model "$model_dir"/Qwen3.6-35B-A3B-UD-Q8_K_XL.gguf \
    --spec-type draft-mtp \
    --spec-draft-n-max 3 \
    --ctx-size 16384 \
    --parallel 4 \
    --temp 0.7 \
    --top-k 20 \
    --min-p 0.0 \
    --presence-penalty 1.5 \
    --repeat-penalty 1.0 \
    --reasoning off


    # --model "$model_dir"/Qwen3.8-27B-UD-Q8_K_XL.gguf \
    # --model-draft "$model_dir"/mtp-Qwen3.8-27B-Q4_0.gguf \
    # --models-preset preset.ini \
