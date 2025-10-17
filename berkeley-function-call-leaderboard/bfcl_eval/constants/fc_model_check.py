import re
from pathlib import Path

config_file = Path("model_config.py")


def extract_dict_block(text, dict_name):
    m = re.search(rf"{dict_name}\s*=\s*\{{", text)
    if not m:
        return None
    start = m.end()
    depth, i = 1, start
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return text[start:i - 1] if depth == 0 else None


ENTRY_RE = re.compile(
    r"""
    ^\s*
    (?P<q>['"])
    (?P<key>(?:\\.|[^'"])+)
    \1
    \s*:\s*
    ModelConfig\s*\(
    (?P<body>.*?)
    \)
    \s*,?\s*$
    """,
    re.DOTALL | re.MULTILINE | re.VERBOSE
)


def get_field(body, field):
    m1 = re.search(rf"{field}\s*=\s*(?P<q>['\"])(?P<val>(?:\\.|[^'\"\\])*)\1", body)
    if m1:
        return bytes(m1.group("val"), "utf-8").decode("unicode_escape")
    m2 = re.search(rf"{field}\s*=\s*(True|False)", body)
    if m2:
        return True if m2.group(1) == "True" else False
    return None


def parse_block(block):
    entries = []
    for m in ENTRY_RE.finditer(block):
        key, body = m.group("key"), m.group("body")
        entries.append({
            "key": key,
            "model_name": get_field(body, "model_name"),
            "display_name": get_field(body, "display_name"),
            "is_fc_model": get_field(body, "is_fc_model"),
            "underscore_to_dot": get_field(body, "underscore_to_dot"),
        })
    return entries


def main():
    repo_root = Path(__file__).resolve().parent
    path = repo_root / config_file
    if not path.exists():
        alt = repo_root / "constants" / "model_config.py"
        if alt.exists():
            path = alt
        else:
            raise SystemExit(f"Config file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")

    blocks = {}
    for name in ["api_inference_model_map", "local_inference_model_map", "third_party_inference_model_map"]:
        blocks[name] = extract_dict_block(text, name)

    records = []
    for name, block in blocks.items():
        if not block:
            continue
        for r in parse_block(block):
            r["dict_name"] = name
            records.append(r)

    def has_fc_marker(r):
        s = lambda x: x or ""
        return ("FC" in s(r["key"])) or ("FC" in s(r["model_name"])) or ("FC" in s(r["display_name"]))

    errors, warnings = [], []
    for r in records:
        marker, is_fc = has_fc_marker(r), r["is_fc_model"]
        if marker and is_fc is False:
            errors.append(r)
        elif not marker and is_fc is True:
            warnings.append(r)
        elif is_fc is None:
            warnings.append(r)

    print("ERRORS (FC, but is_fc_model=False"))
    for r in errors:
        print(f"{r['dict_name']}: key='{r['key']}' | model_name='{r['model_name']}' "
              f"| display_name='{r['display_name']}' | is_fc_model={r['is_fc_model']}")

    print("WARNINGS (no FC, but is_fc_model=True"))
    for r in warnings:
        print(f"{r['dict_name']}: key='{r['key']}' | model_name='{r['model_name']}' "
              f"| display_name='{r['display_name']}' | is_fc_model={r['is_fc_model']}")


if __name__ == "__main__":
    main()
