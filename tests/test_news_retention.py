from datetime import datetime, timezone, timedelta
from news_retention import retain_current_sources

NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)

def row(source, age, identifier, **extra):
    return dict(quelleName=source,title='Article '+identifier,link='https://example.org/'+identifier,
                pubDate=(NOW-timedelta(days=age)).isoformat(),content='WRN metadata',**extra)

def test_later_small_source_survives_large_feed_and_repeated_fast_checkpoints():
    large=[row('Frequent',i/10000,str(i)) for i in range(2100)]
    small=row('Reviewed',15,'older-current',importMode='metadata-only',image='',images=[],contentComplete=False)
    rows=large+[small]
    selected=retain_current_sources(rows,['Frequent','Reviewed'],now=NOW)
    assert len(selected)==2000 and small in selected
    assert sum(r['quelleName']=='Reviewed' for r in selected)==1
    assert small==next(r for r in selected if r['quelleName']=='Reviewed')
    assert retain_current_sources(selected,['Frequent','Reviewed'],now=NOW)==selected
    assert retain_current_sources(list(reversed(rows)),['Frequent','Reviewed'],now=NOW)==selected

def test_expiry_withdrawal_future_and_ungoverned_sources_do_not_get_a_reserved_slot():
    recent=[row('Frequent',0,'latest'),row('Frequent',1,'next')]
    invalid=[row('Reviewed',31,'expired'),row('Reviewed',-1,'future'),
             row('Reviewed',2,'withdrawn',status='withdrawn'),row('Reviewed',2,'deleted',deleted=True)]
    unconfigured=row('Unconfigured',20,'unconfigured')
    selected=retain_current_sources(recent+invalid+[unconfigured],['Frequent','Reviewed'],limit=2,now=NOW)
    assert selected==recent
    assert retain_current_sources(recent,['Frequent'],limit=0,now=NOW)==[]

def test_actual_checkpoint_uses_source_retention_before_atomic_publication(tmp_path):
    import ast
    import time
    from pathlib import Path
    source=Path(__file__).resolve().parents[1]/'aggregate.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    checkpoint=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='save_checkpoint')
    large=[row('Frequent',i/10000,str(i)) for i in range(2100)]
    small=row('Reviewed',15,'original-only',importMode='metadata-only',contentComplete=False,image='',images=[])
    outputs={}
    namespace={'_LAST_CHECKPOINT_AT':0,'CHECKPOINT_INTERVAL_SECONDS':30,'time':time,
        'archiv_dict':{r['link']:r for r in large+[small]},'date_value':__import__('build_web_feeds').date_value,
        'repair_overbroad_archive_categories':lambda r:r,'ARTICLE_MIN_LENGTHS':{},'safe_lower':lambda s:s.lower(),
        'content_is_incomplete':lambda *args:True,'incomplete_limit_for_source':lambda source:3000,
        'retain_current_sources':lambda rows,names:retain_current_sources(rows,names,now=NOW),
        'quellen':{'Asia':[{'name':'Reviewed'},{'name':'Frequent'}]},
        'atomic_json_write':lambda name,rows:outputs.update({name:rows})}
    exec(compile(ast.Module(body=[checkpoint],type_ignores=[]),str(source),'exec'),namespace)
    assert namespace['save_checkpoint'](force=True)
    assert len(outputs['news.json'])==2000
    assert next(r for r in outputs['news.json'] if r['quelleName']=='Reviewed')==small
    namespace['archiv_dict']={r['link']:r for r in outputs['news.json']}
    previous=outputs['news.json']
    assert namespace['save_checkpoint'](force=True)
    assert outputs['news.json']==previous
