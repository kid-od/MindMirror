UPLOAD_STAGES = [
    ("uploading", "上传文件"),
    ("parsing", "解析文档"),
    ("chunking", "生成分块"),
    ("embedding", "生成向量"),
    ("indexing", "写入知识库"),
]


def build_upload_progress_event(stage: str, detail: str = "", state: str = "running") -> dict:
    stage_keys = [item[0] for item in UPLOAD_STAGES]
    if stage not in stage_keys:
        raise ValueError(f"unknown upload stage: {stage}")
    if state not in {"running", "completed", "error"}:
        raise ValueError(f"unknown upload state: {state}")

    current_index = stage_keys.index(stage)
    total_steps = len(UPLOAD_STAGES)

    stages = []
    for index, (key, label) in enumerate(UPLOAD_STAGES):
        if index < current_index:
            status = "done"
        elif index > current_index:
            status = "pending"
        else:
            if state == "completed":
                status = "done"
            elif state == "error":
                status = "error"
            else:
                status = "active"
        stages.append({"key": key, "label": label, "status": status})

    completed_steps = current_index if state != "completed" else current_index + 1
    progress_percent = int(completed_steps / total_steps * 100)

    return {
        "type": "progress",
        "stage": stage,
        "label": dict(UPLOAD_STAGES)[stage],
        "detail": detail,
        "state": state,
        "step_index": current_index + 1,
        "total_steps": total_steps,
        "progress_percent": progress_percent,
        "stages": stages,
    }
