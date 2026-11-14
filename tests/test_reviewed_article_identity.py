"""Strict source-bound re-entry protection for seven verified URL identities."""
import ast
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest
import build_source_archive as b
import build_web_feeds as w
from news_retention import retain_current_sources
from reviewed_article_identity import (REVIEWED_HTTP_IDENTITIES as RULES,
    canonicalize_reviewed_link, canonicalize_reviewed_articles)

TITLES = {'http://www.democracynow.org/2026/11/10/pete_hegseth_impeachment_risk': 'Pentagon Whistleblower Wes Bryant: Impeach Hegseth. He\'s a "Clear & Present Danger" to Democracy', 'http://www.democracynow.org/2026/11/9/stephen_miller_chief_of_staff': '"Hatemonger" as Chief of Staff: Trump Taps Stephen Miller to Top Role After Massive Election Defeat', 'http://www.democracynow.org/2026/11/6/mississippi_senate_election_southern_us_shift': 'Purple Mississippi? Overcoming GOP Voter Suppression, Black Voters Power Dem Wins Across the South', 'http://www.democracynow.org/2026/11/5/2026_midterm_election_overview': 'The Country Says "No" to Trump: Not Just Congress, the Blue Tsunami Flips Statehouses Across U.S.', 'http://www.democracynow.org/2026/11/4/keisha_lance_bottoms_becomes_first_black': '"Over a Decade of Organizing": Keisha Lance Bottoms Elected First Black Woman Governor in U.S. History', 'http://www.democracynow.org/2026/11/3/midterm_ballot_measures': '"Democracy Itself Is on the Ballot": Voters Weigh 150+ Ballot Initiatives, from Wealth Tax to Abortion', 'http://www.democracynow.org/2026/11/2/matthew_cole_jared_kushner_book': '"Princes and Thieves" Author Matthew Cole on Jared Kushner & the "Secret Plot to Remake Middle East"'}
NOW = datetime(2026,11,14,2,tzinfo=timezone.utc)

def article(old=None,**extra):
    old = old or next(iter(RULES));r=RULES[old]
    return dict(quelleName=r['source'],title=TITLES[old],link=old,pubDate=r['pubDate'],
                content='CURRENT BODY ' * 200,contentComplete=True,**extra)

@pytest.mark.parametrize('old',list(RULES))
def test_exact_http_identity_changes_only_scheme_and_iso_date_is_supported(old):
    row=article(old);original=copy.deepcopy(row)
    out=canonicalize_reviewed_articles([row]);assert row==original
    assert out==[dict(row,link=RULES[old]['to'])]
    stamp=b.parse_date(row['pubDate']).isoformat()
    assert canonicalize_reviewed_link(old,row['quelleName'],row['title'],stamp)==RULES[old]['to']
    assert canonicalize_reviewed_articles(out)==out

@pytest.mark.parametrize('change',[{'quelleName':'Another source'},{'title':'Different'},
    {'pubDate':'2026-11-10T12:00:00Z'},{'pubDate':'2026-11-10T13:15:35'},
    {'pubDate':None},{'title':None}])
def test_changed_or_incomplete_reviewed_identity_is_not_guessed(change):
    row=article();row.update(change);before=copy.deepcopy(row)
    with pytest.raises(ValueError,match='identity changed'):canonicalize_reviewed_articles([row])
    assert row==before

@pytest.mark.parametrize('kind',['body','restriction','date','title'])
def test_conflicting_alias_pair_is_not_order_dependent(kind):
    row=article();other=dict(row,link=RULES[row['link']]['to'])
    if kind=='body':other['content']='OTHER BODY'
    elif kind=='restriction':other['importMode']='metadata-only'
    elif kind=='date':other['pubDate']='2026-11-11T00:00:00Z'
    else:other['title']='Changed canonical title'
    for rows in ([row,other],[other,row]):
        with pytest.raises(ValueError,match='Conflicting'):canonicalize_reviewed_articles(rows)


def test_identical_aliases_deduplicate_but_unreviewed_urls_do_not_change():
    row=article();new=dict(row,link=RULES[row['link']]['to'])
    assert canonicalize_reviewed_articles([row,new,row])==[new]
    for url in ['http://www.democracynow.org/unreviewed','http://foreign.example/a',
                row['link']+'?x=1',row['link']+'#fragment',row['link'].replace('www.','')]:
        unknown=dict(row,link=url);assert canonicalize_reviewed_articles([unknown])==[unknown]


def test_current_incomplete_revision_and_withdrawals_win_over_old_full_body():
    row=article();old=dict(row,link=RULES[row['link']]['to'])
    current=dict(row,content='incomplete now',contentComplete=False)
    _,chunks=b.build_source_archives([current],[],previous_articles=[old],generated_at=NOW)
    actual=next(iter(chunks.values()))[0]
    assert actual['link']==old['link'] and actual['content']=='incomplete now' and actual['contentComplete'] is False
    for key in (row['link'],old['link']):
        manifest,chunks=b.build_source_archives([row],[],previous_articles=[old],withdrawn_keys={key},generated_at=NOW)
        assert manifest['itemCount']==0 and chunks=={}
    tombstone=dict(row,status='withdrawn')
    _,chunks=b.build_source_archives([row],[tombstone],previous_articles=[old],generated_at=NOW)
    assert chunks=={}


def test_source_policy_still_restricts_reentered_http_row():
    row=article();policy=dict(name=row['quelleName'],homepage='https://www.democracynow.org/',importMode='metadata-only')
    _,chunks=b.build_source_archives([row],[],source_policies=[policy],generated_at=NOW)
    actual=next(iter(chunks.values()))[0]
    assert actual['link']==RULES[row['link']]['to'] and actual['importMode']=='metadata-only'
    assert 'CURRENT BODY' not in actual['content'] and actual['contentComplete'] is False


def test_checkpoint_retention_never_returns_reviewed_http_or_silent_conflict():
    row=article();new=dict(row,link=RULES[row['link']]['to'])
    assert retain_current_sources([row,new],[row['quelleName']],now=NOW)==[new]
    with pytest.raises(ValueError,match='Conflicting'):
        retain_current_sources([row,dict(new,content='changed')],[row['quelleName']],now=NOW)


def test_archive_cli_rejects_conflict_before_any_output_change(tmp_path,monkeypatch):
    from news_archive_capture import capture_news_archive
    monkeypatch.setattr(b,'ROOT',tmp_path);monkeypatch.setattr(sys,'argv',['build_source_archive.py'])
    row=article();b.write_payload(tmp_path/'news.json',[row]);b.write_payload(tmp_path/'news-feed.json',[row])
    manifest,_=b.build_source_archives([],[],generated_at=datetime.now(timezone.utc))
    b.write_payload(tmp_path/'news-archive-manifest.json',manifest)
    b.write_payload(tmp_path/'feed-status.json',{'news':{}})
    capture_news_archive([row],tmp_path/'news-archive-capture.json',[],allow_initialize=True)
    b.write_payload(tmp_path/'multilingual-source-registry.json',{'sources':[]});b.main()
    before={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*.json') if p.name!='news.json'}
    b.write_payload(tmp_path/'news.json',[row,dict(row,link=RULES[row['link']]['to'],content='CONFLICT')])
    with pytest.raises(ValueError,match='Conflicting'):b.main()
    assert before=={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob('*.json') if p.name!='news.json'}


def test_web_feed_rejects_conflict_before_any_output_change(tmp_path,monkeypatch):
    row=article();news=tmp_path/'news.json';w.atomic_json(news,[row,dict(row,link=RULES[row['link']]['to'],content='CONFLICT')])
    monkeypatch.setattr(w,'NEWS_SOURCE',news)
    targets=[]
    for name in ['NEWS_TARGET','EVENTS_TARGET','STATUS_TARGET']:
        path=tmp_path/(name+'.json');path.write_text('UNCHANGED');monkeypatch.setattr(w,name,path);targets.append(path)
    with pytest.raises(ValueError,match='Conflicting'):w.main()
    assert all(p.read_text()=='UNCHANGED' for p in targets)


def test_actual_ingress_call_precedes_lookup_and_outside_load_recovery_handler():
    source=(Path(__file__).resolve().parents[1]/'aggregate.py').read_text()
    tree=ast.parse(source)
    call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='canonicalize_reviewed_link')
    lookup=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='existing_article' for t in n.targets))
    assert call.lineno<lookup.lineno
    assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.DictComp) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='canonicalize_reviewed_articles' for x in ast.walk(n)))
    assert assignment in tree.body
    # Exercise the actual feed-entry prefix, not the network aggregation loop.
    handler=next(n for n in ast.walk(tree) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='original_link' for t in x.targets) for x in n.body))
    prefix=[]
    for node in handler.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='event_start' for t in node.targets):break
        prefix.append(node)
    wrapped=ast.Module(body=[ast.For(target=ast.Name(id='entry',ctx=ast.Store()),iter=ast.Name(id='entries',ctx=ast.Load()),body=prefix,orelse=[])],type_ignores=[])
    row=article();scope={'entries':[{'link':row['link'],'title':row['title'],'published':row['pubDate']}],
        'is_radar':False,'feed_name':row['quelleName'],'TARGET_ARTICLE_LINKS':{RULES[row['link']]['to']},
        'safe_text':lambda v,default='':str(v) if v else default,'datetime':datetime,'canonicalize_reviewed_link':canonicalize_reviewed_link}
    exec(compile(ast.fix_missing_locations(wrapped),'actual-ingress-prefix','exec'),scope)
    assert scope['link']==RULES[row['link']]['to']


def test_actual_entry_handler_propagates_reviewed_identity_failure_instead_of_continuing():
    from reviewed_article_identity import ReviewedArticleIdentityError
    source=(Path(__file__).resolve().parents[1]/'aggregate.py').read_text();tree=ast.parse(source)
    handler=next(n for n in ast.walk(tree) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='original_link' for t in x.targets) for x in n.body))
    prefix=[]
    for node in handler.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='event_start' for t in node.targets):break
        prefix.append(node)
    actual=ast.Try(body=prefix,handlers=handler.handlers,orelse=[],finalbody=[])
    wrapped=ast.Module(body=[ast.For(target=ast.Name(id='entry',ctx=ast.Store()),iter=ast.Name(id='entries',ctx=ast.Load()),body=[actual],orelse=[])],type_ignores=[])
    row=article();logged=[]
    scope={'entries':[{'link':row['link'],'title':'CHANGED TITLE','published':row['pubDate']}],
        'is_radar':False,'feed_name':row['quelleName'],'TARGET_ARTICLE_LINKS':set(),
        'safe_text':lambda v,default='':str(v) if v else default,'datetime':datetime,
        'canonicalize_reviewed_link':canonicalize_reviewed_link,'ReviewedArticleIdentityError':ReviewedArticleIdentityError,
        'log_feed_entry_error':lambda *args:logged.append(args)}
    with pytest.raises(ReviewedArticleIdentityError):exec(compile(ast.fix_missing_locations(wrapped),'actual-entry-handler','exec'),scope)
    assert logged==[]


@pytest.mark.parametrize('split_files',[False,True])
def test_actual_archive_load_rejects_conflict_before_dict_erases_it(tmp_path,monkeypatch,split_files):
    import os
    from reviewed_article_identity import ReviewedArticleIdentityError
    source=(Path(__file__).resolve().parents[1]/'aggregate.py').read_text();tree=ast.parse(source)
    load=next(n for n in tree.body if isinstance(n,ast.Try) and any(isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='archive_file' for x in n.body))
    finalize=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.DictComp) and any(isinstance(x,ast.Name) and x.id=='_loaded_archive_rows' for x in ast.walk(n)))
    row=article();changed=dict(row,content='CONFLICTING SAME URL')
    (tmp_path/'news.json').write_text(json.dumps([row] if split_files else [row,changed]))
    (tmp_path/'events.json').write_text(json.dumps([changed] if split_files else []))
    monkeypatch.chdir(tmp_path);printed=[]
    scope={'os':os,'json':json,'archiv_dict':{},'_loaded_archive_rows':[],'gesehene_titel':set(),
        'canonicalize_reviewed_articles':canonicalize_reviewed_articles,'ReviewedArticleIdentityError':ReviewedArticleIdentityError,
        'print':lambda *args:printed.append(args)}
    with pytest.raises(ReviewedArticleIdentityError):exec(compile(ast.fix_missing_locations(ast.Module(body=[load,finalize],type_ignores=[])),'actual-archive-load','exec'),scope)
    assert printed==[]


@pytest.mark.parametrize('target',['http','https','unrelated'])
def test_actual_targeted_refresh_accepts_only_either_reviewed_spelling(target):
    source=(Path(__file__).resolve().parents[1]/'aggregate.py').read_text();tree=ast.parse(source)
    handler=next(n for n in ast.walk(tree) if isinstance(n,ast.Try) and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='original_link' for t in x.targets) for x in n.body))
    prefix=[]
    for node in handler.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='event_start' for t in node.targets):break
        prefix.append(node)
    prefix+=ast.parse('accepted = True').body
    wrapped=ast.Module(body=[ast.For(target=ast.Name(id='entry',ctx=ast.Store()),iter=ast.Name(id='entries',ctx=ast.Load()),body=prefix,orelse=[])],type_ignores=[])
    row=article();destination={'http':row['link'],'https':RULES[row['link']]['to'],'unrelated':'https://example.org/unrelated'}[target]
    scope={'entries':[{'link':row['link'],'title':row['title'],'published':row['pubDate']}],
        'is_radar':False,'feed_name':row['quelleName'],'TARGET_ARTICLE_LINKS':{destination},'accepted':False,
        'safe_text':lambda v,default='':str(v) if v else default,'datetime':datetime,'canonicalize_reviewed_link':canonicalize_reviewed_link}
    exec(compile(ast.fix_missing_locations(wrapped),'actual-target-prefix','exec'),scope)
    assert scope['accepted'] is (target!='unrelated')
