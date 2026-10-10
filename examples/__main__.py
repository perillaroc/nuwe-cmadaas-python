"""Run offline examples and map legacy script paths to their replacements."""

import argparse
from importlib import import_module
import json
from pathlib import Path

from .catalog import EXAMPLES


def load_legacy_migration():
    path = Path(__file__).with_name("legacy-migration.json")
    records = json.loads(path.read_text(encoding="utf-8"))["scripts"]
    by_path = {record["legacy_path"]: record for record in records}
    if len(by_path) != len(records):
        raise ValueError("Duplicate legacy script path")
    return by_path


def resolve_legacy(path):
    path = path.replace("\\", "/")
    for prefix in ("example/nuwe_cmadaas_example/", "nuwe_cmadaas_example/"):
        if path.startswith(prefix):
            path = path.removeprefix(prefix)
            break
    try:
        return load_legacy_migration()[path]
    except KeyError as exc:
        raise ValueError(f"Unknown legacy script: {path}") from exc


def run_example(name):
    module, function, _ = EXAMPLES[name]
    result = getattr(import_module("examples." + module), function)()
    print(f"{name}: synthetic contracts passed")
    return result


def render_legacy_index():
    lines = [
        "# 旧脚本迁移索引", "",
        "本文件由 `python -m examples --write-migration-index` 从",
        "[legacy-migration.json](../examples/legacy-migration.json) 生成。",
        "旧路径相对于 `example/nuwe_cmadaas_example/`。所有替代命令从仓库根目录执行，",
        "默认只运行人工数据；历史资料代码及非日期原生参数保存在 JSON 中，不代表当前授权或接口能力。", "",
        "也可使用 `python -m examples --legacy music/.../script.py` 按旧路径选择替代场景，",
        "原 interface、响应方法和格式保持对应。旧 Click 参数不传给这个选择入口。", "",
        "| 旧脚本 | MUSIC interface / 方法 | 新命令 |", "| --- | --- | --- |",
    ]
    for path, record in load_legacy_migration().items():
        command = "python -m examples.music.scenarios " + record["scenario"]
        if record["operation"] != "query":
            command += " --operation " + record["operation"]
        if record["format"]:
            command += " --format " + record["format"]
        lines.append(f"| [{path}](nuwe_cmadaas_example/{path}) | `{record['interface_id']}` / `{record['method']}` | `{command}` |")
    lines += ["", "配置、真实服务替换与兼容退出条件见 [旧包入口](README.md) 和 [统一示例说明](../examples/README.md)。", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", nargs="?", choices=EXAMPLES)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="list offline entry points")
    group.add_argument("--all", action="store_true", help="validate all offline examples and native scenarios")
    group.add_argument("--legacy", metavar="PATH", help="run the offline replacement for an old script")
    group.add_argument("--write-migration-index", action="store_true", help="regenerate example/MIGRATION.md")
    args = parser.parse_args(argv)
    if args.example and (args.list or args.all or args.legacy or args.write_migration_index):
        parser.error("choose an example or a selector flag")
    if args.list:
        for name, (_, _, entries) in EXAMPLES.items():
            print(f"{name}: {', '.join(entries)}")
        print("Native scenarios: python -m examples.music.scenarios --help")
    elif args.legacy:
        from .music.scenarios import run_scenario
        try:
            record = resolve_legacy(args.legacy)
        except ValueError as exc:
            parser.error(str(exc))
        run_scenario(record["scenario"], record["operation"], record["format"] or "json")
    elif args.write_migration_index:
        path = Path(__file__).resolve().parents[1] / "example/MIGRATION.md"
        path.write_text(render_legacy_index(), encoding="utf-8")
        print("Updated example/MIGRATION.md")
    elif args.all:
        from .music.scenarios import SCENARIOS, run_scenario
        for name in EXAMPLES:
            run_example(name)
        for name in SCENARIOS:
            run_scenario(name)
    elif args.example:
        run_example(args.example)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
