"""Exercise answer normalization and evaluation across all five exercise types."""

import json
import re
import unicodedata
from typing import Any, Optional


def normalize_text(text: Any, remove_accents: bool = True) -> str:
    """Normalize text according to locked blueprint rules.

    1. Unicode NFKD
    2. strip combining marks (if remove_accents=True)
    3. lowercase
    4. strip punctuation
    5. collapse whitespace
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # 1. Unicode NFKD
    nfkd = unicodedata.normalize("NFKD", text)

    # 2. strip combining marks if requested
    if remove_accents:
        s = "".join(c for c in nfkd if not unicodedata.combining(c))
    else:
        s = nfkd

    # 3. lowercase
    s = s.lower()

    # 4. strip punctuation (replace non-alphanumeric with spaces,
    # preserving letters from all scripts)
    s = re.sub(r"[^\w\s]", " ", s)

    # 5. collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def evaluate_exercise(
    exercise_type: str,
    payload_json_str: str,
    answer_json_str: str,
    user_answer: Any,
) -> tuple[bool, Any, Optional[str]]:
    """Evaluate a user answer against the authoritative answer definition.

    Returns:
        (is_correct, correct_answer_display, explanation)
    """
    try:
        payload = (
            json.loads(payload_json_str) if isinstance(payload_json_str, str) else payload_json_str
        )
    except Exception:
        payload = {}

    try:
        answer_spec = (
            json.loads(answer_json_str) if isinstance(answer_json_str, str) else answer_json_str
        )
    except Exception:
        answer_spec = {}

    if exercise_type == "multiple_choice":
        # Target answer is a string or dict
        correct_option = answer_spec.get("correct_option", "")
        # Client can pass string, option_id, or dict {"option_id": ...} or {"text": ...}
        if isinstance(user_answer, dict):
            cand = (
                user_answer.get("text")
                or user_answer.get("option_id")
                or user_answer.get("answer")
                or ""
            )
        elif isinstance(user_answer, int):
            # If 0-indexed or 1-indexed option index
            options = payload.get("options", [])
            if 0 <= user_answer < len(options):
                cand = options[user_answer]
            elif 1 <= user_answer <= len(options):
                cand = options[user_answer - 1]
            else:
                cand = str(user_answer)
        else:
            cand = str(user_answer or "")

        norm_cand_acc = normalize_text(cand, remove_accents=False)
        norm_target_acc = normalize_text(correct_option, remove_accents=False)

        if norm_cand_acc == norm_target_acc:
            return True, correct_option, None

        norm_cand_no_acc = normalize_text(cand, remove_accents=True)
        norm_target_no_acc = normalize_text(correct_option, remove_accents=True)

        if norm_cand_no_acc == norm_target_no_acc:
            return True, correct_option, "Pay attention to accents."

        return False, correct_option, None

    elif exercise_type == "fill_blank":
        correct_option = answer_spec.get("correct_option", "")
        if isinstance(user_answer, dict):
            cand = (
                user_answer.get("text")
                or user_answer.get("option_id")
                or user_answer.get("answer")
                or ""
            )
        else:
            cand = str(user_answer or "")

        norm_cand_acc = normalize_text(cand, remove_accents=False)
        norm_target_acc = normalize_text(correct_option, remove_accents=False)

        if norm_cand_acc == norm_target_acc:
            return True, correct_option, None

        norm_cand_no_acc = normalize_text(cand, remove_accents=True)
        norm_target_no_acc = normalize_text(correct_option, remove_accents=True)

        if norm_cand_no_acc == norm_target_no_acc:
            return True, correct_option, "Pay attention to accents."

        return False, correct_option, None

    elif exercise_type == "type_answer":
        accepted_list = answer_spec.get("accepted_answers", [])
        if isinstance(user_answer, dict):
            cand = user_answer.get("text") or user_answer.get("answer") or ""
        else:
            cand = str(user_answer or "")

        norm_cand_acc = normalize_text(cand, remove_accents=False)
        norm_cand_no_acc = normalize_text(cand, remove_accents=True)

        # Check exact (with accents preserved)
        for accepted in accepted_list:
            if norm_cand_acc == normalize_text(accepted, remove_accents=False):
                return True, accepted_list[0] if accepted_list else "", None

        # Check accent-insensitive match
        for accepted in accepted_list:
            if norm_cand_no_acc == normalize_text(accepted, remove_accents=True):
                return True, accepted_list[0] if accepted_list else "", "Pay attention to accents."

        display = accepted_list[0] if accepted_list else ""
        return False, display, None

    elif exercise_type == "translate":
        tokens = answer_spec.get("tokens", [])
        accepted_sequences = answer_spec.get("accepted_token_sequences", [tokens])
        correct_display = " ".join(tokens)

        # Candidate can be tokens list or string
        if isinstance(user_answer, dict):
            cand_tokens = user_answer.get("tokens", [])
        elif isinstance(user_answer, list):
            cand_tokens = user_answer
        elif isinstance(user_answer, str):
            cand_tokens = user_answer.strip().split()
        else:
            cand_tokens = []

        cand_str = " ".join(str(t) for t in cand_tokens)
        norm_cand_acc = normalize_text(cand_str, remove_accents=False)
        norm_cand_no_acc = normalize_text(cand_str, remove_accents=True)

        # Check against all accepted sequences
        for seq in accepted_sequences:
            seq_str = " ".join(str(t) for t in seq)
            if norm_cand_acc == normalize_text(seq_str, remove_accents=False):
                return True, correct_display, None

        for seq in accepted_sequences:
            seq_str = " ".join(str(t) for t in seq)
            if norm_cand_no_acc == normalize_text(seq_str, remove_accents=True):
                return True, correct_display, "Pay attention to accents."

        return False, correct_display, None

    elif exercise_type == "match_pairs":
        expected_matches = answer_spec.get("matches", {})
        if isinstance(user_answer, dict):
            user_matches = user_answer.get("matches", user_answer)
        else:
            user_matches = {}

        if not isinstance(user_matches, dict):
            return False, expected_matches, None

        is_all_correct = True
        for left_id, right_id in expected_matches.items():
            if user_matches.get(left_id) != right_id:
                is_all_correct = False
                break

        return is_all_correct, expected_matches, None

    # Fallback unknown exercise type
    return False, "", None
