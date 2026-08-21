"""定位「创作 skill」bilibili-finance-video 的 workspace/。

发布后数据脚本住在本 skill（danchaofan-data-tracker），但产出要写回创作 skill
的 workspace/（视频文件夹、账号数据/、reports/ 都在那边，是创作 skill 所有）。
cookie 仍读本 skill 根目录（跟着脚本一起搬过来了），只有 workspace 需要回指。

解析顺序：环境变量 BILIBILI_FINANCE_SKILL_DIR > ~/.claude > ~/.codex > 同级目录。
"""
import os


def creation_skill_dir():
    """返回 bilibili-finance-video 技能根目录（workspace/ 的父目录）。"""
    env = os.environ.get("BILIBILI_FINANCE_SKILL_DIR")
    if env and os.path.isdir(env):
        return env
    for base in ("~/.claude/skills/bilibili-finance-video",
                 "~/.codex/skills/bilibili-finance-video"):
        p = os.path.expanduser(base)
        if os.path.isdir(p):
            return p
    # 兜底：本 skill 的同级目录（假设两个 skill 平铺在同一 skills/ 下）
    sibling = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "bilibili-finance-video",
    )
    return sibling


def workspace_root():
    """返回创作 skill 下的 workspace/ 绝对路径。"""
    return os.path.join(creation_skill_dir(), "workspace")
