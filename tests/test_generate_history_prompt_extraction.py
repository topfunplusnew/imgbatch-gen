from src.api.routes import generate


def test_resolve_unified_history_prompt_restores_wrapped_user_prompt_with_numbers():
    wrapped_prompt = """
System instructions:
You are an expert prompt writer.

Latest user request:
生成4张招生图，包含课程亮点、适合人群、学习成果和报名引导，视觉醒目。
类型：海报设计
风格：扁平
这是第1/4张

Final grounded generation brief:
Create an enrollment poster with strong visual hierarchy.
""".strip()

    assert generate._resolve_unified_history_prompt(wrapped_prompt) == (
        "生成4张招生图，包含课程亮点、适合人群、学习成果和报名引导，视觉醒目。 "
        "类型：海报设计 风格：扁平 这是第1/4张"
    )


def test_resolve_unified_history_prompt_prefers_explicit_display_prompt_from_extra_params():
    prompt = "System instructions:\nWrapped prompt"
    extra_params = {
        "display_prompt": "生成4张招生图 类型：海报设计 风格：扁平 这是第1/4张",
    }

    assert generate._resolve_unified_history_prompt(prompt, extra_params) == extra_params["display_prompt"]
