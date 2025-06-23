document.getElementById('runCode').addEventListener('click', function() {
    const html = document.getElementById('htmlCode').value;
    const css = document.getElementById('cssCode').value;
    const js = document.getElementById('jsCode').value;

    const output = document.getElementById('output');
    output.srcdoc = `
        <html>
            <head>
                <style>${css}</style>
            </head>
            <body>
                ${html}
                <script>${js}<\/script>
            </body>
        </html>
    `;
});

document.getElementById('clearCode').addEventListener('click', function() {
    document.getElementById('htmlCode').value = '';
    document.getElementById('cssCode').value = '';
    document.getElementById('jsCode').value = '';
    document.getElementById('output').srcdoc = '';
});
