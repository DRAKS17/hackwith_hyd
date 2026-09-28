const fs = require('fs');

let html = fs.readFileSync('frontend/index.html', 'utf8');

const newLogic = 
                    function escapeHTML(str) {
                        return str.replace(/[&<>'\""]/g, tag => ({
                            '&': '&amp;', '<': '&lt;', '>': '&gt;', \"'\": '&#39;', '\"\"': '&quot;'
                        }[tag] || tag));
                    }
                    
                    let safeHTML = escapeHTML(data.raw_memory);
                    // Convert markdown-like structures securely
                    safeHTML = safeHTML.replace(/### (.*?)\\\\n\\\\n/g, '<h3>$1</h3>\\n<ol>\\n');
                    safeHTML = safeHTML.replace(/(\\\\d+)\\\\. \\\\*\\\\*\\\\[(.*?)\\\\]\\\\*\\\\* (.*?)(?=\\\\n|$)/g, '<li><strong>[$2]</strong> $3</li>\\n');
                    if (safeHTML.includes('<ol>')) {
                        safeHTML += '</ol>';
                    }
                    
                    document.getElementById(\"memory-raw\").innerHTML = safeHTML;
;

html = html.replace(/document\.getElementById\(\"memory-raw\"\)\.innerHTML = data\.raw_memory.*?;/g, newLogic);
fs.writeFileSync('frontend/index.html', html);
