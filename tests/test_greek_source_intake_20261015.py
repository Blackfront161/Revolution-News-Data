import ast
from pathlib import Path
from source_import_policy import metadata_article
from build_sources_registry import normalize_record

SOURCE=Path(__file__).resolve().parents[1]/'aggregate.py'
TREE=ast.parse(SOURCE.read_text(encoding='utf-8'))
FEEDS=ast.literal_eval(next(n.value for n in TREE.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='quellen' for t in n.targets)))['Europe']

def test_reviewed_greek_feed_metadata_retains_existing_endpoints():
    for name,home in [('Apatris','https://apatris.org/'),('Alerta','https://www.alerta.gr/'),('Infolibre','https://infolibre.gr/'),('OmniaTV','https://omniatv.com/')]:
        rows=[r for r in FEEDS if r['name']==name+' (GR)']
        assert len(rows)==1
        assert rows[0]['url']==home+'feed/'
        assert rows[0]['languages']==['el']
        assert rows[0]['languageSource']=='publisher-rss'
        assert 'importMode' not in rows[0], 'language correction must not silently change existing rights'


def test_new_greek_sources_import_only_headlines_and_same_publisher_links():
    for name in ['Alterthess (GR)','The Press Project (GR)','Aftoleksi (GR)','Reporters United (GR)']:
        rows=[r for r in FEEDS if r['name']==name];assert len(rows)==1
        feed=rows[0]
        record=metadata_article(feed,{'title':'Δοκιμή πηγής','link':feed['homepage']+'checked-story/','summary':'FOREIGN SUMMARY','content':[{'value':'FOREIGN FULL TEXT'}],'image':'https://example.org/picture.jpg'},'Europe')
        assert record['language']=='el' and record['importMode']=='metadata-only'
        assert record['contentComplete'] is False and record['images']==[] and record['image']==''
        assert 'FOREIGN' not in str(record)
        assert metadata_article(feed,{'title':'Wrong origin','link':'https://unrelated.example/story'},'Europe') is None
        indexed=normalize_record(feed,origin='aggregate.py',inherited_category='Europe')
        assert indexed['languages']==['el'] and indexed['active']
        assert indexed['importMode']=='metadata-only'


def test_blocked_and_stale_publishers_are_not_promoted():
    urls={row['url'] for row in FEEDS}
    assert 'https://athens.indymedia.org/rss/' in urls
    for host in ['mpalothia.net','efsyn.gr','info-war.gr']:
        assert not any(host in url for url in urls)
