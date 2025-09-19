// generateWasmHttpModule.js

// Define the AssemblyScript code template
const assemblyScriptCode = `
    export function httpRequest(url: string): string {
        const response = fetch(url);
        return 'HTTP request to ' + url + ' initiated';
    }
`;

// Function to compile AssemblyScript to WebAssembly
async function compileAssemblyScript(assemblyScriptCode) {
    const response = await fetch('https://cdn.jsdelivr.net/npm/assemblyscript@0.18.21/dist/asc.js');
    const ascText = await response.text();

    const ascModule = await new Promise(resolve => {
        const script = document.createElement('script');
        script.textContent = ascText;
        script.onload = () => resolve(asc);
        document.head.appendChild(script);
    });

    ascModule.ready.then(async asc => {
        // Write the AssemblyScript code to a file
        const { TextEncoder, TextDecoder } = require('util');
        const fs = require('fs');
        fs.writeFileSync('httpCaller.ts', assemblyScriptCode);

        // Compile AssemblyScript to WebAssembly
        await asc.main(['httpCaller.ts', '-b', 'httpCaller.wasm']);
    });
}

// Function to load and interact with the WebAssembly module
async function loadWebAssembly(url) {
    const response = await fetch('httpCaller.wasm');
    const buffer = await response.arrayBuffer();
    const module = await WebAssembly.compile(buffer);
    const instance = await WebAssembly.instantiate(module);

    // Call the httpRequest function from the WebAssembly module
    const result = instance.exports.httpRequest(url);
    console.log(result);
}

// Usage example: pass google.com as the URL to ping
const url = 'https://www.google.com';
compileAssemblyScript(assemblyScriptCode)
    .then(() => loadWebAssembly(url))
    .catch(error => {
        console.error('Error:', error);
    });
