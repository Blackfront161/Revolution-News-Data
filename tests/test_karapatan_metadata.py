import json
from pathlib import Path
from source_import_policy import metadata_article, restrict_existing_article
ROOT = Path(__file__).resolve().parents[1]
def test_reviewed_philippine_source_retains_only_same_host_metadata():
    source = next(r for r in json.loads((ROOT/'multilingual-source-registry.json').read_text(encoding='utf-8'))['sources'] if r['name']=='Karapatan (Human Rights)')
    entry = {'title':'Publisher headline','link':'https://www.karapatan.org/5561/','published':'Fri, 18 Sep 2026 05:16:12 +0000','summary':'PROTECTED','content':[{'value':'PROTECTED'}],'media_content':[{'url':'https://www.karapatan.org/photo.jpg'}]}
    row=metadata_article(source,entry,'Asia')
    assert row['originCountryCode']=='PH' and row['primaryRegion']=='Asia'
    assert row['link']==entry['link'] and row['pubDate']==entry['published']
    assert not row['contentComplete'] and not row['image'] and not row['images']
    assert 'PROTECTED' not in json.dumps(row)
    assert metadata_article(source,{**entry,'link':'https://foreign.example/5561/'},'Asia') is None
    old={**row,'id':'existing-id','content':'PROTECTED','contentComplete':True,'image':'https://www.karapatan.org/photo.jpg'}
    restricted=restrict_existing_article(old,[source])
    assert restricted['id']=='existing-id' and 'PROTECTED' not in json.dumps(restricted)
def test_topics_require_individual_headline_and_original_binding():
    source = next(r for r in json.loads((ROOT/'multilingual-source-registry.json').read_text(encoding='utf-8'))['sources'] if r['name']=='Karapatan (Human Rights)')
    for title,url in [('Contribution to the 2026 International Ecumenical Peace Convocation Seoul, Republic of Korea','https://www.karapatan.org/5549/'),('Karapatan Monitor for April to June 2026','https://www.karapatan.org/5543/'),('Changed publisher title','https://www.karapatan.org/5561/')]:
        row=metadata_article(source,{'title':title,'link':url},'Asia')
        assert row['primaryTopic']=='Movement News'
        assert 'Indigenous Struggles' not in row['categories'] and 'Anti-Rep & Prisons' not in row['categories']
    row=metadata_article(source,{'title':'Primer on Desaparecidos','link':'https://www.karapatan.org/5561/'},'Asia')
    assert row['primaryTopic']=='Anti-Rep & Prisons' and 'Indigenous Struggles' not in row['categories']
def test_feed_redirect_cannot_fetch_a_foreign_host_or_downgrade():
    import importlib.util
    import urllib.request
    import pytest
    spec=importlib.util.spec_from_file_location('reviewed_karapatan',ROOT/'scripts/refresh-reviewed-karapatan.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    for url in ['https://foreign.example/feed/','http://www.karapatan.org/feed/','https://secret@www.karapatan.org/feed/']:
        with pytest.raises(ValueError): module.SamePublisherRedirect().redirect_request(urllib.request.Request('https://www.karapatan.org/feed/'),None,302,'Found',{},url)
