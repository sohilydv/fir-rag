"""LLM answer generation for retrieved FIR context."""

import requests

def ask_ollama(prompt, model="llama3"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]

# import os
# from typing import List, Dict

# from openai import OpenAI


# def build_prompt(query: str, contexts: List[Dict]) -> str:
#     context_block = "\n\n".join(
#         [f"[Rank {item['rank']}] {item['text']}" for item in contexts]
#     )
#     return (
#         "You are a legal assistant for FIR analysis. "
#         "Use only the provided context. If context is insufficient, say so.\n\n"
#         f"Context:\n{context_block}\n\n"
#         f"Question: {query}\n"
#         "Answer:"
#     )


# def generate_answer(query: str, contexts: List[Dict], model: str) -> str:
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         return "OPENAI_API_KEY is not set. Retrieved context is ready, but no LLM response was generated."

#     client = OpenAI(api_key=api_key)
#     prompt = build_prompt(query, contexts)

#     response = client.responses.create(
#         model=model,
#         input=prompt,
#     )
#     return response.output_text
