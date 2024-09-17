# Building a WASM instance to execute API calls in python (to be produced by the Gorilla LLM)

There are 2 main approaches of executing the API calls in-browswer. The first is pyodide (which has more support overall), and the second is Brython (only supports python built-in features and modules).

Summary of approaches (examples given in `pyodide_examples` directory): 

| Month    | Pyodide | Brython
| -------- | ------- | -------
| REST API  | Yes    | No     |
| numpy | Yes     | No     |
| sqlalchemy    | Yes    | No    |
| pymysql/sqlite3    | No    | No     |
| os.() - file operations    | Yes    | No     |
| Tensorflow / Pytorch / Hugging Face  |   No  | No     |


## Approach 1 - Pyodide (Recommended for most feature coverage)
Pyodide is a python distribution for the browswer based in Web Assembly.

Not all packages are available for use in Pyodide. This is the list of packages built into Pyodide: https://pyodide.org/en/stable/usage/packages-in-pyodide.html

Also, any pure python library (a package on pypi with a pure python wheel) can be used with pyodide. Therefore, packages like tensorflow which are not included on Pyodide yet are not available for use.

Example of using python in Pyodide:
```html
<!doctype html>
<html>
  <head>
      <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
  </head>
  <body>
    <input id="number" value="10" />
    <button onclick="evaluatePython()">Run</button>

    <div id="output"></div>
    <script type="text/javascript">
        const number = document.getElementById("number");
    
      async function main(){
        let pyodide = await loadPyodide();
        return pyodide;
      }
      let pyodideReadyPromise = main();

      async function evaluatePython() {
        let pyodide = await pyodideReadyPromise;
        try {
            await pyodide.loadPackage("micropip");
            await pyodide.loadPackage("numpy");
            let python_output = pyodide.runPython("\nimport micropip \n'numpy' in micropip.list() \nimport numpy as np \nnp.arange(" + number.value + ")")
            console.log(python_output);
            var output_div = document.getElementById('output');
            output_div.innerHTML = python_output;
        } catch (err) {
            console.log(err);
        }
      }

    </script>
  </body>
</html>
```

## Approach 2 - Brython (Easy interaction with webpage elements)

Brython is a way to replace javascript programming with python (on the client side). 

However, it makes it difficult to import packages which are not included with the standard python distribution (ex: numpy etc).

Brython does it make it extremeley easy to interact with the content on the webpage within python (displaying animations or results from python code easily).

Example code:
```html
<html>

<head>
    <meta charset="utf-8">
    <script type="text/javascript"
        src="https://cdn.jsdelivr.net/npm/brython@3.12.0/brython.min.js">
    </script>
    <script type="text/javascript"
        src="https://cdn.jsdelivr.net/npm/brython@3.12.0/brython_stdlib.js">
    </script>
</head>

<body>

<script type="text/python">
from browser import document
import math

print(math.sqrt(9))
print("Hello World")
string = "Hello World. SQRT of 9 is " + str(math.sqrt(9)) 
document <= string</script>
</body>
</html>
```

## Approach 3 - Hosting Python Webserver and Making an Ajax Call

This is the traditional approach of setting up a Flask or Node.js webserver (Node.js can spawn and run python scripts) with an exposed endpoint. The front end can make an API call to the backend with input data as a parameter, and receive the gorilla API call result.

