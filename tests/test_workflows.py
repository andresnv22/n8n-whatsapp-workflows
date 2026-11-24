"""Static validation tests for exported n8n workflow JSON files."""

import json
import re
from pathlib import Path

import pytest

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"
WORKFLOW_FILES = sorted(WORKFLOWS_DIR.glob("*.json"))

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{30,}"),
    re.compile(r"EAAG[0-9A-Za-z]{20,}"),
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),
]


def test_workflows_exist():
    assert len(WORKFLOW_FILES) >= 3


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_workflow_structure_and_connections(path: Path):
    raw = path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(raw), f"Potential secret found in {path.name}"

    data = json.loads(raw)
    assert isinstance(data.get("name"), str) and data["name"].strip()
    assert data.get("active") is False

    nodes = data.get("nodes")
    assert isinstance(nodes, list) and len(nodes) >= 2

    names = [n["name"] for n in nodes]
    ids = [n["id"] for n in nodes]
    assert len(names) == len(set(names)), f"Duplicate node names in {path.name}"
    assert len(ids) == len(set(ids)), f"Duplicate node ids in {path.name}"

    for node in nodes:
        assert node.get("type"), f"Missing type in {node}"
        pos = node.get("position")
        assert isinstance(pos, list) and len(pos) == 2

    node_set = set(names)
    connections = data.get("connections", {})
    assert isinstance(connections, dict) and connections
    for src, outputs in connections.items():
        assert src in node_set, f"Unknown source node '{src}' in {path.name}"
        for branch_list in outputs.get("main", []):
            for edge in branch_list:
                assert edge["node"] in node_set, f"Unknown target node '{edge['node']}' in {path.name}"
