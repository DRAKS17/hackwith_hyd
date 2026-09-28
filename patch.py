import re
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
replacement = """                    function escapeHTML(str) {
                        return str.replace(/[&<>'"]/g, function(tag) {
                            const chars = { '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' };
                            return chars[tag] || tag;
                        });
                    }
                    let safeHTML = escapeHTML(data.raw_memory);
                    safeHTML = safeHTML.replace(/### (.*?)\\n\\n/g, "<h3>$1</h3>\\n<ol>\\n");
                    safeHTML = safeHTML.replace(/(\\d+)\\. \\*\\*\\[(.*?)\\]\\*\\* (.*?)(?=\\n|$)/g, "<li><strong>[$2]</strong> $3</li>\\n");
                    if (safeHTML.includes("<ol>")) { safeHTML += "</ol>"; }
                    document.getElementById("memory-raw").innerHTML = safeHTML;"""

target = 'document.getElementById("memory-raw").innerHTML = data.raw_memory.replace(/\\n/g, "<br>").replace(/\\*\\*(.*?)\\*\\*/g, "<strong>$1</strong>").replace(/### (.*?)<br>/g, "<h3>$1</h3>");'

text = text.replace(target, replacement)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
