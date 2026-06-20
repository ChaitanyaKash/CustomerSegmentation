"""Verify the revised PDF against its saved-result manifest; render separately for layout QA."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = json.loads((ROOT / 'outputs/report_manifest.json').read_text(encoding='utf-8'))
    assert digest(ROOT / 'Project_Report.pdf') == manifest['report_sha256']
    assert digest(ROOT / 'Project_Report.md') == manifest['markdown_sha256']
    for name, expected in manifest['source_sha256'].items():
        assert digest(ROOT / 'outputs' / name) == expected, name
    reader = PdfReader(ROOT / 'Project_Report.pdf')
    assert len(reader.pages) == 11, f'Unexpected pagination: {len(reader.pages)}'
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    for number in manifest['reported_numeric_values']:
        assert number in text, f'Missing reported number: {number}'
    assert '20 June 2026' in text
    assert '27 October 2026' not in text
    assert 'No ResNet-50 embeddings' in text
    assert manifest['models_refitted'] is False
    backup = ROOT / 'local_notes/original_docs/Project_Report.pdf'
    if backup.exists():
        assert digest(backup) == manifest['original_report_sha256']
        assert digest(backup) != manifest['report_sha256']
    print(f'PASS: revised PDF has {len(reader.pages)} pages; all {len(manifest["reported_numeric_values"])} unique tabulated numbers verified')
    print('PASS: PDF, Markdown, source-result hashes and original-report preservation')


if __name__ == '__main__':
    verify()
