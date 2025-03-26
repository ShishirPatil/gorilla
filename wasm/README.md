# WebAssembly HTTP Caller
This project demonstrates how to create a WebAssembly (WASM) module that can execute an HTTP call in the browser. It includes an AssemblyScript template embedded in a JavaScript file (generateWasm.js) that dynamically compiles the AssemblyScript code to WebAssembly and loads the module. The project also includes an HTML file (index.html) that serves as the entry point for the web application.

## Usage
- Edit the generateWasm.js file to modify the AssemblyScript template or the URL for the HTTP request.
- Run a local web server to serve the files. For example, you can use the http-server package:
```csharp
npm install --global http-server
http-server
```
- Open a web browser and navigate to the URL of the index.html file (e.g., http://localhost:8080/index.html).
- Open the browser's developer console to view the output of the HTTP request function

## How It Works
- The generateWasm.js file includes an AssemblyScript code template as a string (assemblyScriptCode), which defines an httpRequest function.
- The compileAssemblyScript function fetches the AssemblyScript compiler (asc.js), compiles the AssemblyScript code to WebAssembly, and saves the resulting httpCaller.wasm file.
- The loadWebAssembly function loads the httpCaller.wasm file, compiles it, instantiates it, and then calls the httpRequest function from the WebAssembly module.

## Example
The provided example demonstrates how to ping google.com. You can modify the url variable in the generateWasm.js file to test with different URLs.
