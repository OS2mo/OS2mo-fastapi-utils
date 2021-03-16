<!--
SPDX-FileCopyrightText: Magenta ApS

SPDX-License-Identifier: MPL-2.0
-->

# OS2MO-FastAPI-Utils

Utility library with various reusable FastAPI components.


## Usage
Install into your project using `pip`:
```
pip install os2mo-fastapi-utils
```

Then import it inside a Python file:
```
from fastapi import FastAPI
from os2mo_fastapi_utils.tracing import setup_instrumentation

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

app = setup_instrumentation(app)
```
