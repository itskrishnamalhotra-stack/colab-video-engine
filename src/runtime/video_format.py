"""One explicit full-HD format contract for portrait and landscape projects."""
import json
from pathlib import Path

FORMATS = {'portrait': (1080, 1920), 'landscape': (1920, 1080)}


def format_dimensions(name='portrait'):
    if name not in FORMATS:
        raise ValueError('Video format must be portrait or landscape.')
    return FORMATS[name]


def project_dimensions(project):
    script = json.loads((Path(project)/'script.json').read_text(encoding='utf-8-sig'))
    name = script.get('format', 'portrait')
    return format_dimensions(name)
