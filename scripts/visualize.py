#!/usr/bin/env python3
"""Export a privacy-safe, zero-dependency Canvas graph explorer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_html(*, nodes: list[dict], edges: list[list[int]], output: Path) -> None:
    # Deliberately serialize only label/type/community — never document text, URLs, or source paths.
    safe_nodes = [
        {"label": str(node.get("label", "Unknown"))[:120], "type": str(node.get("type", "entity"))[:40], "community": int(node.get("community", 0))}
        for node in nodes
    ]
    payload = json.dumps({"nodes": safe_nodes, "edges": edges})
    html = f"""<!doctype html><html><head><!-- HTML5 CanvasRenderingContext2D graph renderer --><meta charset=\"utf-8\"><title>Super Vault Graph</title><style>body{{margin:0;background:#0b1020;color:#edf2f7;font:14px system-ui}}header{{padding:16px 22px;border-bottom:1px solid #263247}}input{{margin-left:12px;padding:8px;border-radius:8px;border:1px solid #40516e;background:#121a2d;color:white}}canvas{{display:block;width:100vw;height:calc(100vh - 61px)}}</style></head><body><header><strong>🧠 Super Vault — Knowledge Graph</strong><input id=\"search\" placeholder=\"Find an entity\"></header><canvas id=\"graph\"></canvas><script>const graph={payload}; const canvas=document.querySelector('#graph'),ctx=canvas.getContext('2d'),search=document.querySelector('#search'); function draw(){{canvas.width=innerWidth;canvas.height=innerHeight-61;ctx.clearRect(0,0,canvas.width,canvas.height);let q=search.value.toLowerCase();graph.nodes.forEach((n,i)=>{{let a=i*Math.PI*2/Math.max(graph.nodes.length,1),r=Math.min(canvas.width,canvas.height)*.34,x=canvas.width/2+Math.cos(a)*r,y=canvas.height/2+Math.sin(a)*r,hit=!q||n.label.toLowerCase().includes(q);ctx.fillStyle=hit?['#7dd3fc','#c4b5fd','#86efac','#fda4af'][n.community%4]:'#273449';ctx.beginPath();ctx.arc(x,y,hit?5:3,0,Math.PI*2);ctx.fill();if(hit&&graph.nodes.length<200){{ctx.fillStyle='#dbeafe';ctx.fillText(n.label,x+7,y+4)}}}})}} search.addEventListener('input',draw);addEventListener('resize',draw);draw();</script></body></html>"""
    Path(output).write_text(html)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a metadata-only Super Vault graph explorer")
    parser.add_argument("--input", required=True, help="JSON: {nodes:[{label,type,community}],edges:[[from,to]]}")
    parser.add_argument("--output", default="super-vault-graph.html")
    args = parser.parse_args()
    graph = json.loads(Path(args.input).read_text())
    build_html(nodes=graph.get("nodes", []), edges=graph.get("edges", []), output=Path(args.output))


if __name__ == "__main__":
    main()
