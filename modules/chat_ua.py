import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import args_manager


@dataclass
class ChatPlan:
    intent: str  # "image" | "none"
    prompt: str
    negative: str
    preset: str
    notes: str = ""


_MODEL = None
_TOKENIZER = None
_PIPELINE_LOAD_ERROR: Optional[str] = None


def _load_llm():
    global _MODEL, _TOKENIZER, _PIPELINE_LOAD_ERROR
    if _MODEL is not None and _TOKENIZER is not None:
        return _MODEL, _TOKENIZER
    if _PIPELINE_LOAD_ERROR is not None:
        raise RuntimeError(_PIPELINE_LOAD_ERROR)

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_id = getattr(args_manager.args, "chat_ua_model", None) or "Qwen/Qwen2.5-0.5B-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        _MODEL, _TOKENIZER = model, tokenizer
        return model, tokenizer
    except Exception as e:
        _PIPELINE_LOAD_ERROR = f"Chat UA model load failed: {e}"
        raise


_EXPLICIT_SEX_RE = re.compile(
    r"\b("
    r"sex|porn|xxx|nude|naked|blowjob|handjob|anal|cum|orgasm|penetrat|rape|incest|child"
    r"|секс|порно|ерот|огол|гол(а|ий)|мінет|анальн|оргазм|ґвалт|зґвалт|інцест|дитин"
    r")\b",
    flags=re.IGNORECASE,
)


def _is_explicit_request(text: str) -> bool:
    return bool(_EXPLICIT_SEX_RE.search(text or ""))


def _system_prompt() -> str:
    return (
        "Ти — асистент у генераторі зображень Fooocus. Відповідай ЛИШЕ українською. "
        "Твоє завдання: з діалогу зробити план генерації.\n"
        "Поверни рівно один JSON-об'єкт без пояснень і без markdown.\n"
        "Схема JSON:\n"
        "{"
        "\"intent\":\"image|none\","
        "\"prompt\":\"...\","
        "\"negative\":\"...\","
        "\"preset\":\"...\","
        "\"notes\":\"...\""
        "}\n"
        "Правила:\n"
        "- Якщо користувач описує кадр/сцену для зображення — intent=image.\n"
        "- preset став \"realistic_cinematic_anatomy\" для фотореалізму з анатомією, якщо не сказано інакше.\n"
        "- negative має уникати дефектів анатомії.\n"
    )


def _messages_to_text(history: List[Tuple[str, str]], user_message: str) -> str:
    lines = []
    for u, a in history[-8:]:
        if u:
            lines.append(f"Користувач: {u}")
        if a:
            lines.append(f"Асистент: {a}")
    lines.append(f"Користувач: {user_message}")
    return "\n".join(lines)


def _extract_json(text: str) -> Dict[str, Any]:
    # Try strict parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Fallback: find first {...}
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        return json.loads(candidate)
    raise ValueError("No JSON found in model output")


def plan_from_chat(history: List[Tuple[str, str]], user_message: str) -> ChatPlan:
    if _is_explicit_request(user_message):
        return ChatPlan(
            intent="none",
            prompt="",
            negative="",
            preset="realistic_cinematic_anatomy",
            notes="Запит містить відвертий сексуальний контент. Переформулюй без відвертої порнографії (18+ деталі не підтримуються).",
        )

    model, tokenizer = _load_llm()
    import torch

    prompt = _system_prompt() + "\n\n" + _messages_to_text(history, user_message)

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.4,
            top_p=0.9,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id,
        )

    decoded = tokenizer.decode(out[0], skip_special_tokens=True)
    # Keep only the tail after the input prompt if possible
    tail = decoded[len(tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)) :].strip()
    if not tail:
        tail = decoded.strip()

    data = _extract_json(tail)

    intent = str(data.get("intent", "none"))
    if intent not in ("image", "none"):
        intent = "none"

    preset = str(data.get("preset", "realistic_cinematic_anatomy") or "realistic_cinematic_anatomy")
    prompt_txt = str(data.get("prompt", "") or "")
    negative_txt = str(
        data.get(
            "negative",
            "bad anatomy, deformed, extra limbs, extra fingers, fused fingers, lowres, blurry",
        )
        or ""
    )
    notes = str(data.get("notes", "") or "")

    return ChatPlan(intent=intent, prompt=prompt_txt, negative=negative_txt, preset=preset, notes=notes)

