const raw_memory_sample = `### Hindsight recalled 3 memories:\n\n1. **[2026-05-20 | topics]** Demo <script>alert(1)</script> conducted. | When: 2026-05-20\n\n2. **[2026-05-20 | objections]** Contact "c1" requested info.\n\n3. **[Unknown | fact]** User & contact discussed ROI.`;

function renderMemoryPanel(raw_memory) {
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, function(tag) {
            const charsToReplace = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            };
            return charsToReplace[tag] || tag;
        });
    }
    
    let safeHTML = escapeHTML(raw_memory);
    // Convert markdown-like structures securely
    safeHTML = safeHTML.replace(/### (.*?)\n\n/g, "<h3>$1</h3>\n<ol>\n");
    safeHTML = safeHTML.replace(/(\d+)\. \*\*\[(.*?)]\*\* (.*?)(?=\n|$)/g, "<li><strong>[$2]</strong> $3</li>\n");
    if (safeHTML.includes("<ol>")) {
        safeHTML += "</ol>";
    }
    
    return safeHTML;
}

console.log("=== ITEM 4: FRONTEND RENDERING OUTPUT ===");
console.log(renderMemoryPanel(raw_memory_sample));
