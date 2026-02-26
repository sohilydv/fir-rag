"""Entry point for FIR RAG: build index and answer queries."""

try:
    from .retriever import retrieve
    from .llm import ask_ollama
except ImportError:
    from retriever import retrieve
    from llm import ask_ollama

def ask_question(query):
    contexts = retrieve(query, k=50)
    if not contexts:
        return "No matching FIR context found."

    context_text = "\n".join(
        [
            f"CaseID: {item.get('case_id', 'NA')} | FIR: {item.get('fir_srno', 'NA')} | "
            f"PS: {item.get('ps', 'NA')}\n{item.get('text', '')}"
            for item in contexts
        ]
    )

    final_prompt = f"""
You are an assistant analysing FIR records of Jharkhand Police.

Use only the provided context to answer.

Context:
{context_text}

Question:
{query}

Answer clearly and factually.
"""

    return ask_ollama(final_prompt)


if __name__ == "__main__":
    print("Ask question mode started.")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        query = input("Ask question: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Exiting Ask question mode.")
            break
        if not query:
            print("Please enter a question, or type 'exit' to quit.")
            continue
        print(ask_question(query))


