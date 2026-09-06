import re

with open('backend/orchestrator/pipeline.py', 'r') as f:
    text = f.read()

text = text.replace('if not findings:', 'print("FINDINGS:", len(findings), [f.title for f in findings])\n        if not findings:')

with open('backend/orchestrator/pipeline.py', 'w') as f:
    f.write(text)
