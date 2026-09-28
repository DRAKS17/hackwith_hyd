import json
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

out = []
out.append('# Proof of Dynamic Memory Adaptation\n')

# We'll test both c1 and c2, forward and backward
contacts = ['c1', 'c2']
stages_fwd = [1, 3, 5]
stages_rev = [5, 3, 1]

for c in contacts:
    out.append(f'## Contact: {c}\n')
    out.append('### Forward Order\n')
    for stage in stages_fwd:
        client.post('/simulate', json={'contact_id': c, 'meeting_number': stage})
        res = client.post('/prep', json={'contact_id': c, 'context': 'next meeting'})
        data = res.json()
        mod = data.get('model_used')
        out.append(f'#### Before meeting {stage}')
        out.append(f'**Model Used:** {mod}')
        out.append('```json\n' + json.dumps(data.get('briefing'), indent=2) + '\n```\n')

    out.append('### Reverse Order (Proving no stale state)\n')
    for stage in stages_rev:
        client.post('/simulate', json={'contact_id': c, 'meeting_number': stage})
        res = client.post('/prep', json={'contact_id': c, 'context': 'next meeting'})
        data = res.json()
        mod = data.get('model_used')
        out.append(f'#### Before meeting {stage}')
        out.append(f'**Model Used:** {mod}')
        out.append('```json\n' + json.dumps(data.get('briefing'), indent=2) + '\n```\n')

with open('../docs/sample_briefings.md', 'w') as f:
    f.write('\n'.join(out))
print('Done generating sample_briefings.md!')
