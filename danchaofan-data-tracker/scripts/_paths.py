"""定位账号级共享工作台 workspace/。

workspace/ 是「蛋炒饭财经」账号级的共享数据（视频文件夹、账号数据/、reports/、
huasheng.md），住在 danchaofan-skills 仓库根，被创作/数据/评论多个 skill 共同读写，
不再从属于任何单个 skill。发布后数据脚本住在本 skill（danchaofan-data-tracker），
产出写回这个共享 workspace/。cookie 仍读本 skill 根目录（跟脚本一起）。

解析顺序：环境变量 DANCHAOFAN_WORKSPACE > 穿透 symlink 回到仓库根的 workspace/。
本 skill 以软链接装进 ~/.claude/skills / ~/.codex/skills 时，realpath 会解回本仓库，
仓库根 = 本文件（skill/scripts/_paths.py）向上三级。
"""
import os


def workspace_root():
    """返回账号级共享工作台 workspace/ 的绝对路径。"""
    env = os.environ.get("DANCHAOFAN_WORKSPACE")
    if env and os.path.isdir(env):
        return env
    # 穿透 symlink 拿到本文件真实路径 → skill/scripts/_paths.py 向上三级 = 仓库根
    here = os.path.realpath(__file__)
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    return os.path.join(repo_root, "workspace")
