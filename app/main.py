"""Entry point for FIR RAG: build index and answer queries."""

try:
    from .act_section_eval import (
        build_act_section_prompt,
        evaluate_prediction,
        extract_predicted_act_section_text,
        is_act_section_query,
    )
    from .ipc_tagger import extract_sections_line
    from .retriever import retrieve
    from .llm import ask_ollama
except ImportError:
    from act_section_eval import (
        build_act_section_prompt,
        evaluate_prediction,
        extract_predicted_act_section_text,
        is_act_section_query,
    )
    from ipc_tagger import extract_sections_line
    from retriever import retrieve
    from llm import ask_ollama


def _ask_act_section_with_accuracy(query, contexts):
    prompt = build_act_section_prompt(query=query, contexts=contexts, max_contexts=8)
    raw_answer = ask_ollama(prompt)
    predicted_text = extract_predicted_act_section_text(raw_answer)

    top_hit = contexts[0]
    evaluation = evaluate_prediction(predicted_text=predicted_text, expected_context=top_hit)
    expected_sections_line = (
        evaluation["expected"]["sections_line"]
        or top_hit.get("sections_line")
        or extract_sections_line(top_hit.get("text", ""))
        or "NA"
    )

    return "\n".join(
        [
            f"Predicted Act Section: {predicted_text or 'Unknown'}",
            f"Expected Act Section (metadata): {expected_sections_line}",
            f"Matched CaseID: {top_hit.get('case_id', 'NA')}",
            f"Accuracy: {evaluation['accuracy']}",
        ]
    )


def ask_question(query):
    contexts = retrieve(query, k=50)
    if not contexts:
        return "No matching FIR context found."

    if is_act_section_query(query):
        return _ask_act_section_with_accuracy(query, contexts)

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
    print("Act-section template: Act section for FIR content: <paste FIR content>")
    while True:
        query = input("Ask question: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("Exiting Ask question mode.")
            break
        if not query:
            print("Please enter a question, or type 'exit' to quit.")
            continue
        print(ask_question(query))

