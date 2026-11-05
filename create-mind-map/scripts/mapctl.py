#!/usr/bin/env python3
"""learnmap state tool: map.json is the source of truth, index.html is rendered from it.

Append-only: once a node has a body, nothing here will overwrite it.
Corrections go in as a new child node with kind=correction.
"""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
PLACEHOLDER = "/*__MAP_DATA__*/null"
KINDS = {"root", "concept", "mechanism", "example", "rationale", "compare",
         "quiz", "feedback", "correction", "term", "factcheck"}
FACT_STATUSES = {"unchecked", "passed", "issues", "not-applicable", "corrected"}
STATUSES = {"stub", "expanded", "known"}
CONFIDENCE = {"verified", "from-memory"}
NODE_FIELDS = ("title", "kind", "summary", "body", "link_to_work",
               "sources", "confidence", "asked_by")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load(map_dir):
    path = Path(map_dir) / "map.json"
    if not path.exists():
        fail(f"{path} not found, run init first")
    return json.loads(path.read_text(encoding="utf-8"))


def save(map_dir, data):
    data["updated"] = date.today().isoformat()
    path = Path(map_dir) / "map.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    render(map_dir, data)


def render(map_dir, data=None):
    data = data or load(map_dir)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        fail("template placeholder missing")
    out = Path(map_dir) / "index.html"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out.write_text(html.replace(PLACEHOLDER, payload).replace("/*__RENDERED__*/", stamp), encoding="utf-8")
    return out


def validate_node(spec, need_parent):
    if need_parent and not spec.get("parent"):
        fail(f"node '{spec.get('title')}' has no parent")
    if not spec.get("title"):
        fail("node without title")
    kind = spec.get("kind", "concept")
    if kind not in KINDS:
        fail(f"kind '{kind}' not in {sorted(KINDS)}")
    conf = spec.get("confidence", "from-memory")
    if conf not in CONFIDENCE:
        fail(f"confidence '{conf}' not in {sorted(CONFIDENCE)}")
    sources = spec.get("sources", [])
    if conf == "verified" and not sources:
        fail(f"node '{spec['title']}' is marked verified but has no sources")


def next_id(data):
    nums = [int(k[1:]) for k in data["nodes"] if k[1:].isdigit()]
    return f"n{max(nums, default=-1) + 1}"


def build_node(spec, parent):
    body = spec.get("body", "").strip()
    return {
        "title": spec["title"],
        "parent": parent,
        "kind": spec.get("kind", "concept"),
        "summary": spec.get("summary", "").strip(),
        "body": body,
        "link_to_work": spec.get("link_to_work", "").strip(),
        "sources": spec.get("sources", []),
        "confidence": spec.get("confidence", "from-memory"),
        "status": "expanded" if body else "stub",
        "children": [],
        "asked_by": spec.get("asked_by", ""),
        "fact_check": {"status": "unchecked"},
        "created": date.today().isoformat(),
    }


def read_json_arg(file_arg):
    raw = sys.stdin.read() if file_arg == "-" else Path(file_arg).read_text(encoding="utf-8")
    return json.loads(raw)


def cmd_init(args):
    map_dir = Path(args.dir)
    if (map_dir / "map.json").exists():
        fail(f"{map_dir}/map.json already exists; resume it instead of re-initialising")
    map_dir.mkdir(parents=True, exist_ok=True)
    root = build_node({"title": args.title, "kind": "root",
                       "summary": args.summary or ""}, None)
    data = {"slug": args.slug, "title": args.title, "context": args.context or "",
            "root": "n0", "created": date.today().isoformat(), "nodes": {"n0": root}}
    save(map_dir, data)
    print(f"created {map_dir}/map.json and index.html")


def cmd_add(args):
    data = load(args.dir)
    specs = read_json_arg(args.file)
    specs = specs if isinstance(specs, list) else [specs]
    created = []
    for spec in specs:
        validate_node(spec, need_parent=True)
        parent = spec["parent"]
        if parent not in data["nodes"]:
            fail(f"parent {parent} does not exist")
        nid = next_id(data)
        data["nodes"][nid] = build_node(spec, parent)
        data["nodes"][parent]["children"].append(nid)
        created.append(nid)
    save(args.dir, data)
    print("added " + " ".join(created))


def cmd_fill(args):
    data = load(args.dir)
    node = data["nodes"].get(args.node)
    if node is None:
        fail(f"node {args.node} does not exist")
    if node["body"]:
        fail(f"{args.node} already has a body (append-only). Add a child node instead, "
             "e.g. kind=correction if something in it is wrong.")
    spec = read_json_arg(args.file)
    if not spec.get("body", "").strip():
        fail("fill needs a non-empty body")
    merged = {**node, **{k: spec[k] for k in NODE_FIELDS if k in spec and k != "title"}}
    merged["title"] = node["title"]
    validate_node(merged, need_parent=False)
    merged["status"] = "expanded"
    data["nodes"][args.node] = merged
    save(args.dir, data)
    print(f"filled {args.node}")


def cmd_status(args):
    if args.set not in STATUSES:
        fail(f"status must be one of {sorted(STATUSES)}")
    data = load(args.dir)
    node = data["nodes"].get(args.node)
    if node is None:
        fail(f"node {args.node} does not exist")
    if args.set == "stub" and node["body"]:
        fail("cannot mark a node with a body as stub")
    data["nodes"][args.node] = {**node, "status": args.set}
    save(args.dir, data)
    print(f"{args.node} -> {args.set}")


def cmd_factcheck(args):
    """Record a fact-check result: a factcheck child with the claim table, plus a status on the node.

    The checked node's body is never touched. Wrong claims get their own correction child.
    """
    allowed = FACT_STATUSES - {"unchecked", "corrected"}
    if args.result not in allowed:
        fail(f"result must be one of {sorted(allowed)} (use `resolve` to mark corrected)")
    data = load(args.dir)
    node = data["nodes"].get(args.node)
    if node is None:
        fail(f"node {args.node} does not exist")
    if not node["body"]:
        fail(f"{args.node} is a stub, nothing to check")
    spec = read_json_arg(args.file) if args.file else {}
    claims = spec.get("claims", [])
    if args.result != "not-applicable" and not claims:
        fail("a checked node needs a claims list: [{claim, verdict, evidence, source}]")
    bad = [c for c in claims if c.get("verdict") not in ("correct", "wrong", "partly", "unverifiable")]
    if bad:
        fail("each claim verdict must be correct / wrong / partly / unverifiable")
    has_wrong = any(c["verdict"] in ("wrong", "partly") for c in claims)
    if args.result == "passed" and has_wrong:
        fail("cannot mark passed while a claim is wrong or partly wrong")
    if args.result == "issues" and not has_wrong:
        fail("result=issues needs at least one wrong or partly claim")

    stamp = {"status": args.result, "date": date.today().isoformat(),
             "checked": len(claims), "wrong": sum(c["verdict"] == "wrong" for c in claims),
             "partly": sum(c["verdict"] == "partly" for c in claims),
             "unverifiable": sum(c["verdict"] == "unverifiable" for c in claims)}
    data["nodes"][args.node] = {**node, "fact_check": stamp}

    if claims:
        label = {"correct": "ถูก", "wrong": "ผิด", "partly": "ถูกบางส่วน", "unverifiable": "ตรวจไม่ได้"}
        rows = ["| # | claim | ผล | หลักฐาน | แหล่ง |", "|---|---|---|---|---|"]

        def cell(v):
            return str(v or "-").replace("|", "\\|").replace("\n", " ")

        for i, c in enumerate(claims, 1):
            rows.append(f"| {i} | {cell(c.get('claim'))} | {label[c['verdict']]} | "
                        f"{cell(c.get('evidence'))} | {cell(c.get('source'))} |")
        summary = (f"ตรวจ {len(claims)} claim: ผิด {stamp['wrong']}, ถูกบางส่วน {stamp['partly']}, "
                   f"ตรวจไม่ได้ {stamp['unverifiable']}")
        note = spec.get("note", "").strip()
        body = "\n".join(rows) + (f"\n\n{note}" if note else "")
        sources = [{"type": "web" if str(c.get("source", "")).startswith("http") else "doc",
                    "ref": c["source"]} for c in claims if c.get("source")]
        child = build_node({"title": f"Fact check: {node['title']}", "kind": "factcheck",
                            "summary": summary, "body": body, "sources": sources,
                            "confidence": "verified" if sources else "from-memory",
                            "asked_by": "fact-check"}, args.node)
        child["fact_check"] = {"status": "not-applicable"}
        nid = next_id(data)
        data["nodes"][nid] = child
        data["nodes"][args.node]["children"].append(nid)
        print(f"factcheck child {nid}")
    save(args.dir, data)
    print(f"{args.node} fact_check -> {args.result}")


def cmd_link(args):
    """Add a purposeful cross-link between two nodes on different branches (append-only)."""
    data = load(args.dir)
    nodes = data["nodes"]
    for nid in (args.src, args.dst):
        if nid not in nodes:
            fail(f"node {nid} does not exist")
    if args.src == args.dst:
        fail("a node cannot link to itself")
    if nodes[args.src]["parent"] == args.dst or nodes[args.dst]["parent"] == args.src:
        fail("these two are parent and child already; a cross-link adds nothing")
    if not args.label.strip() or not args.why.strip():
        fail("every cross-link needs a label (the relationship) and a why (its purpose)")
    links = data.setdefault("links", [])
    if any({link["from"], link["to"]} == {args.src, args.dst} for link in links):
        fail("these two nodes are linked already")
    lid = f"l{len(links)}"
    data["links"] = [*links, {"id": lid, "from": args.src, "to": args.dst, "label": args.label.strip(),
                              "why": args.why.strip(), "created": date.today().isoformat()}]
    save(args.dir, data)
    print(f"linked {lid}: {args.src} --{args.label}--> {args.dst}")


def cmd_resolve(args):
    """Mark an `issues` node as corrected once a fact-checked correction child covers it.

    The original body stays as written; the page shows the correction above it.
    """
    data = load(args.dir)
    nodes = data["nodes"]
    node = nodes.get(args.node)
    if node is None:
        fail(f"node {args.node} does not exist")
    if node.get("fact_check", {}).get("status") != "issues":
        fail(f"{args.node} is not marked as having issues")
    fixes = [c for c in node["children"] if nodes[c]["kind"] == "correction"]
    if not fixes:
        fail(f"{args.node} has no correction child; add one first")
    unchecked = [c for c in fixes if nodes[c].get("fact_check", {}).get("status") not in ("passed", "not-applicable")]
    if unchecked:
        fail(f"correction(s) {unchecked} have not passed a fact check yet")
    stamp = {**node["fact_check"], "status": "corrected", "corrected_by": fixes,
             "corrected_on": date.today().isoformat()}
    data["nodes"][args.node] = {**node, "fact_check": stamp}
    save(args.dir, data)
    print(f"{args.node} -> corrected by {', '.join(fixes)}")


def cmd_unchecked(args):
    """List nodes with a body that nobody has fact-checked yet."""
    data = load(args.dir)
    for nid, n in data["nodes"].items():
        if n["body"] and n.get("fact_check", {}).get("status", "unchecked") == "unchecked":
            print(f"{nid} {n['title']}")


def cmd_path(args):
    """Minimal context for expanding one node: root-to-node chain plus siblings."""
    data = load(args.dir)
    nodes = data["nodes"]
    if args.node not in nodes:
        fail(f"node {args.node} does not exist")
    chain, cur = [], args.node
    while cur is not None:
        chain.append(cur)
        cur = nodes[cur]["parent"]
    chain.reverse()
    print(f"# map: {data['title']}  (context: {data.get('context') or '-'})")
    for depth, nid in enumerate(chain):
        n = nodes[nid]
        print(f"{'  ' * depth}{nid} [{n['kind']}] {n['title']}: {n['summary']}")
    target = nodes[args.node]
    print("\n## target body")
    print(target["body"] or "(stub)")
    if target["link_to_work"]:
        print(f"\n## link_to_work\n{target['link_to_work']}")
    parent = target["parent"]
    if parent:
        sibs = [s for s in nodes[parent]["children"] if s != args.node]
        if sibs:
            print("\n## siblings (do not repeat these)")
            for s in sibs:
                print(f"- {s} {nodes[s]['title']}: {nodes[s]['summary']}")
    touching = [link for link in data.get("links", []) if args.node in (link["from"], link["to"])]
    if touching:
        print("\n## cross-links")
        for link in touching:
            other = link["to"] if link["from"] == args.node else link["from"]
            print(f"- {link['from']} --{link['label']}--> {link['to']} ({nodes[other]['title']}) · why: {link['why']}")
    if target["children"]:
        print("\n## existing children (do not repeat these)")
        for c in target["children"]:
            print(f"- {c} {nodes[c]['title']}: {nodes[c]['summary']}")


def cmd_outline(args):
    data = load(args.dir)
    nodes = data["nodes"]
    mark = {"stub": "o", "expanded": "*", "known": "v"}

    def walk(nid, depth):
        n = nodes[nid]
        fc = n.get("fact_check", {}).get("status", "unchecked")
        unchecked_flag = " [fc:-]" if n["body"] and fc == "unchecked" else ""
        flag = {"passed": " [fc:ok]", "issues": " [fc:ISSUES]", "corrected": " [fc:corrected]"}.get(fc, unchecked_flag)
        print(f"{'  ' * depth}{mark[n['status']]} {nid} {n['title']}  [{n['kind']}]{flag}")
        for c in n["children"]:
            walk(c, depth + 1)

    walk(data["root"], 0)


def cmd_render(args):
    print(render(args.dir))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("dir")
    s.add_argument("--slug", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--summary")
    s.add_argument("--context")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add", help="append child nodes from a JSON list (file or -)")
    s.add_argument("dir")
    s.add_argument("--file", required=True)
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("fill", help="write the body of a stub node (refuses if body exists)")
    s.add_argument("dir")
    s.add_argument("--node", required=True)
    s.add_argument("--file", required=True)
    s.set_defaults(func=cmd_fill)

    s = sub.add_parser("status")
    s.add_argument("dir")
    s.add_argument("--node", required=True)
    s.add_argument("--set", required=True)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("factcheck", help="record fact-check claims + status for a node")
    s.add_argument("dir")
    s.add_argument("--node", required=True)
    s.add_argument("--result", required=True)
    s.add_argument("--file", help="JSON {claims:[...], note} (file or -); optional for not-applicable")
    s.set_defaults(func=cmd_factcheck)

    s = sub.add_parser("link", help="cross-link two nodes with a relationship label and a purpose")
    s.add_argument("dir")
    s.add_argument("--from", dest="src", required=True)
    s.add_argument("--to", dest="dst", required=True)
    s.add_argument("--label", required=True, help="relationship phrase shown on the line, e.g. 'เป็นสาเหตุของ'")
    s.add_argument("--why", required=True, help="why this link helps understanding")
    s.set_defaults(func=cmd_link)

    s = sub.add_parser("resolve", help="mark an issues node corrected (needs a passed correction child)")
    s.add_argument("dir")
    s.add_argument("--node", required=True)
    s.set_defaults(func=cmd_resolve)

    s = sub.add_parser("unchecked")
    s.add_argument("dir")
    s.set_defaults(func=cmd_unchecked)

    for name, fn in (("path", cmd_path), ("outline", cmd_outline), ("render", cmd_render)):
        s = sub.add_parser(name)
        s.add_argument("dir")
        if name == "path":
            s.add_argument("--node", required=True)
        s.set_defaults(func=fn)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
