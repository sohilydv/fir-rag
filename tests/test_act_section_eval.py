from app.act_section_eval import (
    evaluate_prediction,
    extract_predicted_act_section_text,
    is_act_section_query,
)


def test_is_act_section_query_detects_section_intent():
    assert is_act_section_query("Act section for FIR content: accused stole bike from market")
    assert is_act_section_query("इस FIR में कौन सी धारा लगती है?")
    assert not is_act_section_query("केस आईडी से IO का नाम बताओ")


def test_extract_predicted_act_section_text_reads_template_line():
    llm_output = """Some explanation
Predicted_Act_Section: IPC-379, IPC-411
"""
    assert extract_predicted_act_section_text(llm_output) == "IPC-379, IPC-411"


def test_evaluate_prediction_binary_accuracy_one_on_exact_match():
    context = {
        "sections_line": "भारतीय दंड संहिता-379, भारतीय दंड संहिता-411",
        "act_tags": ["IPC_1860"],
        "text": "",
    }
    result = evaluate_prediction("IPC-379, IPC-411", context)
    assert result["accuracy"] == 1
    assert result["section_accuracy"] == 1
    assert result["act_tag_accuracy"] == 1


def test_evaluate_prediction_binary_accuracy_zero_on_mismatch():
    context = {
        "sections_line": "भारतीय दंड संहिता-379, भारतीय दंड संहिता-411",
        "act_tags": ["IPC_1860"],
        "text": "",
    }
    result = evaluate_prediction("IPC-302", context)
    assert result["accuracy"] == 0
