# App Lib Notebooks
* This folder contains experimental notebooks for the App Lib

## Helpful Preamble Cells
- The following python code provides commonly used imports and can be helpful as a first cell for Python notebooks.

``` python
%load_ext autoreload
%autoreload 2
import os
import sys

from dotenv import load_dotenv
from IPython.display import Markdown, display
from loguru import logger

load_dotenv()
```