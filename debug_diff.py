import re

with open('core/diff.py', 'r') as f:
    text = f.read()

text = text.replace(
    "if abs(c1.null_fraction - c2.null_fraction) > 0.0001:",
    "print(f'c1={c1}, c2={c2}')\n              if abs(c1.null_fraction - c2.null_fraction) > 0.0001:"
)

with open('core/diff.py', 'w') as f:
    f.write(text)
