---
name: ai-util-jupyter
description: "Create simple, focused Jupyter notebooks that demonstrate a single concept or technique. Use this skill when the user asks to 'create a notebook', 'make a Jupyter notebook', 'demo this in a notebook', 'prototype this', 'prove this concept', 'show me how X works in a notebook', 'write a notebook for', 'explore this in a notebook', or 'demonstrate this technique'. Also trigger when someone wants to verify logic, test an idea, or create a quick proof-of-concept using Python. Do NOT use for full application code, production scripts, or comprehensive tutorials — notebooks created by this skill are intentionally minimal."
model: sonnet
effort: medium
---

# Jupyter Notebook Creator

Create simple, minimal Jupyter notebooks that demonstrate one concept clearly. The goal is a notebook someone can read top-to-bottom in under two minutes and immediately understand what it shows.

A notebook that tries to cover too much defeats its own purpose. When a reader has to wade through helper functions, multiple examples, and edge case handling before seeing the core idea, the concept gets buried. Keep it small enough that the concept is impossible to miss.

## Workflow

1. Identify the single concept or technique the user wants to demonstrate
2. Determine the simplest possible sequence of cells that shows it working
3. Write the notebook using the cell structure below
4. Stop — do not add bonus examples, variations, or "while we're at it" content

## Cell Structure

Every notebook follows this pattern:

```
[Title cell — markdown]
[Brief intro — markdown, 2-4 sentences max]
[Preamble cell — code, ALWAYS included]
[Optional: additional imports cell — code]
[Concept cell pair: markdown explanation + code] × N
[Optional: result/output summary — markdown]
```

## Preamble Cell

Every notebook MUST include this preamble as the first code cell, immediately after the intro markdown cell:

```python
import os, sys
from IPython.display import HTML, Image, Markdown, display
from dotenv import load_dotenv
from loguru import logger
load_dotenv()

%load_ext autoreload
%autoreload 2
```

This cell is mandatory and must not be omitted or modified. Any additional imports needed for the notebook go in a separate cell after the preamble.

Keep N small. Two or three concept cell pairs is usually enough. If you're writing a fifth pair, reconsider the scope.

## Writing Code Cells

Write logic directly in the cell body. A cell should read like a short script, not a function call.

**Prefer this:**
```python
data = [1, 2, 3, 4, 5]
squared = [x ** 2 for x in data]
print(squared)
```

**Over this:**
```python
def square_list(lst):
    return [x ** 2 for x in lst]

result = square_list([1, 2, 3, 4, 5])
print(result)
```

The inline version shows the logic immediately. The function version makes the reader look in two places.

Functions in cells are appropriate when the user specifically asks for a function, when the same operation genuinely needs to run multiple times in the notebook, or when the function itself *is* the concept being demonstrated (e.g., a recursive algorithm). In those cases, define and call the function in the same cell when possible.

## Writing Markdown Cells

Each code cell gets one markdown cell above it. Keep it to 1-3 sentences that answer: "what is this cell doing and why?"

**Good markdown cell:**
```
List comprehensions let us transform a list in a single readable expression.
Here we square each number in a list without a loop.
```

**Too verbose:**
```
In Python, there are several ways to transform lists. You can use for loops,
map(), or list comprehensions. List comprehensions are generally preferred
for readability. They follow the pattern [expression for item in iterable].
We'll use this pattern to square numbers, though the same technique applies
to strings, filtering, nested lists, and many other cases...
```

The markdown cell is a signpost, not a tutorial. If the user wants depth, they'll ask.

## Scope Discipline

Only demonstrate what was requested. If the user says "show me how to read a CSV with pandas", the notebook reads a CSV. It does not also show filtering, grouping, plotting, or exporting — unless asked.

When in doubt, do less and offer to expand. "I kept this focused on X — let me know if you'd like to add Y" is better than a sprawling notebook the user has to trim down.

## Output

Use the `Write` tool to create a `.ipynb` file at the path the user specifies, or ask for a path if none was given. Use the `NotebookEdit` tool when adding or modifying individual cells in an existing notebook.

Structure the notebook JSON with:
- `"nbformat": 4`, `"nbformat_minor": 5`
- Markdown cells: `"cell_type": "markdown"`
- Code cells: `"cell_type": "code"` with `"outputs": []` and `"execution_count": null`

After creating the file, briefly summarize what the notebook demonstrates and how many cells it has.
