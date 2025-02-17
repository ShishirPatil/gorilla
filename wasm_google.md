# WebAssembly Ping Google Example
This repository contains a simple example of using WebAssembly (WASM) to execute an HTTP request to ping google.com directly in the browser.

## JavaScript Code
```javascript
// JavaScript code to execute HTTP request in the browser

// Function to execute HTTP request and ping google.com
function pingGoogle() {
    // Perform HTTP GET request to google.com
    fetch('https://www.google.com')
    .then(response => {
        // Check if response status is OK
        if (response.ok) {
            console.log('Ping successful');
        } else {
            console.error('Failed to ping Google');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Export the function to be called from WebAssembly
exports.pingGoogle = pingGoogle;
```

## AssemblyScript Code
```typescript
// AssemblyScript code to call the JavaScript function

// Import the JavaScript function
declare function pingGoogle(): void;

// Export a function to be called from JavaScript
export function wasmPingGoogle(): void {
    // Call the imported JavaScript function
    pingGoogle();
}
```

## Compiling the WebAssembly Module
```bash
asc wasmPingGoogle.ts -b wasmPingGoogle.wasm --exportRuntime
```

## Using the WebAssembly Module
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebAssembly Ping Google Example</title>
</head>
<body>
    <h1>WebAssembly Ping Google Example</h1>
    <p>Check browser console for ping result</p>

    <script>
        // Load WebAssembly module
        const { wasmPingGoogle } = require('./wasmPingGoogle');

        // Call the exported function
        wasmPingGoogle();
    </script>
</body>
</html>
```
