import ast
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import news_archive_capture as capture
from news_retention import retain_current_sources
from reviewed_article_identity import REVIEWED_HTTP_IDENTITIES

NOW = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)


def row(i=1, **changes):
    return dict({"link": f"https://source.test/article-{i}", "title": f"Article {i}",
                 "quelleName": "Source", "pubDate": (NOW - timedelta(hours=1)).isoformat(),
                 "content": "Complete body " * 100, "contentComplete": True}, **changes)


def write(path, rows):
    path.write_text(json.dumps(rows), encoding="utf-8")


def test_pre2000_rollover_and_replay(tmp_path):
    path = tmp_path / "capture.json"
    initial = [row(i) for i in range(2500)]
    saved = capture.capture_news_archive(initial, path, [], now=NOW, allow_initialize=True)
    bounded = retain_current_sources(initial, ["Source"], now=NOW)
    assert len(bounded) == 2000 and len(saved) == 2500
    after = capture.capture_news_archive(bounded + [row(2501)], path, [], now=NOW + timedelta(hours=1))
    assert len(after) == 2501
    assert {r["link"]: r["content"] for r in after}.items() >= {r["link"]: r["content"] for r in initial}.items()
    before = path.read_bytes()
    capture.capture_news_archive(bounded + [row(2501)], path, [], now=NOW + timedelta(hours=1))
    assert path.read_bytes() == before


def test_body_revision_history_is_bound_and_immutable(tmp_path):
    path = tmp_path / "capture.json"
    original = row()
    first = capture.capture_news_archive([original], path, [], now=NOW, allow_initialize=True)
    revised = row(content="Corrected and complete body " * 50)
    second = capture.capture_news_archive([revised], path, [], now=NOW + timedelta(hours=1))
    history = second[0][capture.HISTORY]
    assert second[0]["content"] == revised["content"]
    assert history[0]["body"] == original["content"]
    assert history[0]["bodySha256"] == hashlib.sha256(original["content"].encode()).hexdigest()
    third = capture.capture_news_archive([revised], path, [], now=NOW + timedelta(hours=2))
    assert third[0][capture.HISTORY] == history
    assert capture.HISTORY not in first[0]


@pytest.mark.parametrize("field,value", [("title", "Other title"), ("quelleName", "Other source"),
                                          ("pubDate", "2026-11-14T10:00:00Z")])
def test_identity_change_aborts_without_writes(tmp_path, field, value):
    path = tmp_path / "capture.json"; write(path, [row()]); original = path.read_bytes()
    with pytest.raises(ValueError, match="identity changed"):
        capture.capture_news_archive([row(**{field: value})], path, [], now=NOW)
    assert path.read_bytes() == original


def test_full_to_different_partial_aborts(tmp_path):
    path = tmp_path / "capture.json"; write(path, [row()]); original = path.read_bytes()
    with pytest.raises(ValueError, match="changed to partial"):
        capture.capture_news_archive([row(content="Partial body", contentComplete=False)], path, [], now=NOW)
    assert path.read_bytes() == original


def test_identical_body_flag_downgrade_does_not_borrow_complete():
    result = capture.merge_capture_rows([row()], [row(contentComplete=False)], [], now=NOW)
    assert result[0]["content"] == row()["content"]
    assert result[0]["contentComplete"] is False


def test_tombstone_survives_replay_and_expiry(tmp_path):
    path = tmp_path / "capture.json"; write(path, [row()])
    withdrawn = capture.capture_news_archive([row(status="withdrawn")], path, [], now=NOW)
    assert withdrawn[0]["content"] == "" and withdrawn[0]["deleted"] is True
    assert capture.HISTORY not in withdrawn[0]
    replay = capture.capture_news_archive([row()], path, [], now=NOW + timedelta(days=29))
    assert replay == withdrawn
    assert capture.capture_news_archive([], path, [], now=NOW + timedelta(days=31)) == []


def test_history_removed_by_metadata_policy_and_cannot_be_reactivated(tmp_path):
    path = tmp_path / "capture.json"; write(path, [row()])
    revised = row(content="Updated complete body " * 100)
    capture.capture_news_archive([revised], path, [], now=NOW)
    policies = [{"name": "Source", "homepage": "https://source.test/", "importMode": "metadata-only"}]
    result = capture.capture_news_archive([], path, policies, now=NOW)
    assert capture.HISTORY not in result[0] and result[0]["contentComplete"] is False
    assert result[0]["importMode"] == "metadata-only" and revised["content"] not in path.read_text()
    with pytest.raises(ValueError, match="cannot be reactivated"):
        capture.capture_news_archive([revised], path, [], now=NOW)


@pytest.mark.parametrize("policy", [{"name":"Source", "status":"withdrawn"},
                                    {"name":"Source", "importMode":"directory-only"},
                                    {"name":"Source", "importMode":"disabled"}])
def test_restrictive_policy_creates_bodyless_tombstone(policy):
    result = capture.merge_capture_rows([row()], [], [policy], now=NOW)
    assert result[0]["deleted"] is True and result[0]["content"] == ""


def test_technical_fetch_pause_is_not_withdrawal():
    assert capture.merge_capture_rows([row()], [], [{"name":"Source", "enabled":False, "status":"disabled"}], now=NOW)[0]["content"] == row()["content"]


@pytest.mark.parametrize("bad", ["{", "{}", "[null]", '[{"link":"x","link":"y"}]', '[NaN]'])
def test_bad_capture_fail_closed(tmp_path, bad):
    path=tmp_path/"capture.json"; path.write_text(bad)
    with pytest.raises(ValueError): capture.capture_news_archive([row()], path, [], now=NOW, allow_initialize=True)
    assert path.read_text() == bad


def test_missing_capture_requires_explicit_bootstrap(tmp_path):
    path=tmp_path/"capture.json"
    with pytest.raises(ValueError, match="bootstrap"): capture.capture_news_archive([row()], path, [], now=NOW)
    assert not path.exists()
    assert capture.read_capture(path, allow_bootstrap=True) == []


def test_atomic_replace_failure_keeps_existing_file(tmp_path, monkeypatch):
    path=tmp_path/"capture.json"; write(path,[row()]); previous=path.read_bytes()
    def fail(*args): raise OSError("simulated replace failure")
    monkeypatch.setattr(capture.os,"replace",fail)
    with pytest.raises(OSError): capture.capture_news_archive([row(2)],path,[],now=NOW)
    assert path.read_bytes()==previous and list(tmp_path.glob("*.tmp")) == []


def test_atomic_flush_failure_keeps_existing_file(tmp_path, monkeypatch):
    path=tmp_path/"capture.json"; write(path,[row()]); previous=path.read_bytes()
    def fail(*args): raise OSError("simulated fsync failure")
    monkeypatch.setattr(capture.os,"fsync",fail)
    with pytest.raises(OSError): capture.capture_news_archive([row(2)],path,[],now=NOW)
    assert path.read_bytes()==previous and list(tmp_path.glob("*.tmp")) == []


def test_output_and_history_bounds_keep_original(tmp_path, monkeypatch):
    path=tmp_path/"capture.json"; write(path,[row()]); previous=path.read_bytes()
    monkeypatch.setattr(capture,"MAX_CAPTURE_BYTES",len(previous)+20)
    with pytest.raises(ValueError,match="byte limit"):
        capture.capture_news_archive([row(2)],path,[],now=NOW)
    assert path.read_bytes()==previous
    monkeypatch.setattr(capture,"MAX_CAPTURE_BYTES",64*1024*1024)
    capture.capture_news_archive([row(content="Revision 2")],path,[],now=NOW)
    previous=path.read_bytes();monkeypatch.setattr(capture,"MAX_HISTORY_ROWS",1)
    with pytest.raises(ValueError,match="history exceeds"):
        capture.capture_news_archive([row(content="Revision 3")],path,[],now=NOW)
    assert path.read_bytes()==previous


def test_withdrawal_removes_all_previous_bodies(tmp_path):
    path=tmp_path/"capture.json";write(path,[row()])
    capture.capture_news_archive([row(content="New full revision")],path,[],now=NOW)
    result=capture.capture_news_archive([row(status="revoked")],path,[],now=NOW)
    assert capture.HISTORY not in result[0]
    assert row()["content"] not in path.read_text() and "New full revision" not in path.read_text()


def test_restrictive_changed_title_cannot_block_existing_url_withdrawal():
    result=capture.merge_capture_rows([row()], [row(title="Publisher withdrew this item",status="withdrawn")], [], now=NOW)
    assert result[0]["deleted"] is True and result[0]["content"]==""
    assert result[0]["title"]==row()["title"]


def test_bounds_reject_without_truncation(tmp_path, monkeypatch):
    path=tmp_path/"capture.json"; write(path,[row()]); previous=path.read_bytes()
    monkeypatch.setattr(capture,"MAX_CAPTURE_ROWS",1)
    with pytest.raises(ValueError): capture.capture_news_archive([row(2)],path,[],now=NOW)
    assert path.read_bytes()==previous
    monkeypatch.setattr(capture,"MAX_CAPTURE_BYTES",4)
    with pytest.raises(ValueError,match="byte limit"): capture.read_capture(path)
    assert path.read_bytes()==previous


def test_current_cannot_inject_internal_history():
    for field in (capture.HISTORY,capture.WITHDRAWN_AT):
        with pytest.raises(ValueError,match="provenance"):
            capture.merge_capture_rows([], [row(**{field:[]})], [], now=NOW)


def test_history_tamper_and_wrong_identity_rejected(tmp_path):
    path=tmp_path/"capture.json"; write(path,[row()])
    result=capture.capture_news_archive([row(content="New full body")],path,[],now=NOW)
    result[0][capture.HISTORY][0]["body"]="tampered"
    write(path,result)
    with pytest.raises(ValueError,match="hash mismatch"): capture.read_capture(path)


def test_duplicate_conflicting_revisions_and_unknown_policy():
    with pytest.raises(ValueError,match="Conflicting"):
        capture.merge_capture_rows([], [row(),row(content="different")], [], now=NOW)
    with pytest.raises(ValueError,match="Unknown"):
        capture.merge_capture_rows([], [row()], [{"name":"Source","importMode":"invented"}], now=NOW)
    with pytest.raises(ValueError,match="Unknown"):
        capture.merge_capture_rows([], [row(importMode="invented")], [], now=NOW)


def test_window_and_date_validation():
    old=row(1,pubDate=(NOW-timedelta(days=31)).isoformat())
    recent=row(2,pubDate=(NOW-timedelta(days=30)).isoformat())
    future=row(3,pubDate=(NOW+timedelta(days=2)).isoformat())
    assert [r["link"] for r in capture.merge_capture_rows([], [old,recent,future], [], now=NOW)] == [recent["link"]]
    with pytest.raises(ValueError): capture.merge_capture_rows([], [row(pubDate="bad")], [], now=NOW)


def test_checkpoint_capture_precedes_both_caps_and_all_outputs():
    tree=ast.parse((ROOT/"aggregate.py").read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="save_checkpoint")
    seen=[]; writes=[]
    articles=[row(i, contentComplete=i<2400, kontinent="Global") for i in range(2500)]
    class Clock:
        @staticmethod
        def monotonic(): return 10
    env={"time":Clock,"_LAST_CHECKPOINT_AT":0,"CHECKPOINT_INTERVAL_SECONDS":100,
         "archiv_dict":{r["link"]:r for r in articles}, "date_value":lambda r:1,
         "repair_overbroad_archive_categories":lambda r:r,"ARTICLE_MIN_LENGTHS":{},
         "safe_lower":lambda s:s.lower(),"content_is_incomplete":lambda *a:False,
         "incomplete_limit_for_source":lambda s:5,"read_capture_policies":lambda p:[],
         "quellen":{"Global":[{"name":"Source"}]},
         "capture_news_archive":lambda rows,*a:(seen.append(copy.deepcopy(rows)) or rows),
         "public_capture_rows":capture.public_capture_rows,
         "retain_current_sources":lambda rows,*a:rows[:2000],
         "atomic_json_write":lambda path,rows:writes.append((path,len(rows)))}
    exec(compile(ast.Module(body=[node],type_ignores=[]),"checkpoint","exec"),env)
    assert env["save_checkpoint"](True)
    assert len(seen[0])==2500 and sum(r["contentComplete"] is False for r in seen[0])==100
    assert writes[0]==("news.json",2000)
    writes.clear()
    def fail(*args):raise ValueError("capture failed")
    env["capture_news_archive"]=fail
    with pytest.raises(ValueError):env["save_checkpoint"](True)
    assert writes==[]


def test_initial_capture_load_keeps_older_full_articles_known(tmp_path):
    path=tmp_path/'capture.json'
    older=row(10,pubDate=(NOW-timedelta(days=20)).isoformat())
    current=row(20)
    capture.capture_news_archive([older,current],path,[],now=NOW,allow_initialize=True)
    before=path.read_bytes()
    loaded=capture.load_capture_for_aggregation(path,[current],[],now=NOW)
    known={r['link']:r for r in loaded}
    assert known[older['link']]['content']==older['content']
    assert known[older['link']]['contentComplete'] is True
    assert len(known)==2 and path.read_bytes()==before
    # Existing-style aggregation sees the retained URL as known, not a new RSS excerpt.
    assert older['link'] in known


def test_initial_capture_load_strips_history_without_mutating_persistence(tmp_path):
    path=tmp_path/'capture.json'
    capture.capture_news_archive([row()],path,[],now=NOW,allow_initialize=True)
    revised=row(content='A complete revised body '*100)
    capture.capture_news_archive([revised],path,[],now=NOW)
    before=path.read_bytes()
    loaded=capture.load_capture_for_aggregation(path,[revised],[],now=NOW)
    assert loaded[0]['content']==revised['content']
    assert capture.HISTORY not in loaded[0] and capture.WITHDRAWN_AT not in loaded[0]
    assert capture.HISTORY in capture.read_capture(path)[0] and path.read_bytes()==before


def test_initial_capture_load_applies_metadata_and_sticky_tombstones(tmp_path):
    path=tmp_path/'capture.json'
    capture.capture_news_archive([row()],path,[],now=NOW,allow_initialize=True)
    policy=[{'name':'Source','homepage':'https://source.test/','importMode':'metadata-only'}]
    loaded=capture.load_capture_for_aggregation(path,[row()],policy,now=NOW)
    assert loaded[0]['importMode']=='metadata-only' and loaded[0]['contentComplete'] is False
    assert row()['content'] not in json.dumps(loaded)
    withdrawn=capture.capture_news_archive([row(status='withdrawn')],path,[],now=NOW)
    loaded=capture.load_capture_for_aggregation(path,[row()],[],now=NOW+timedelta(days=1))
    assert loaded[0]['deleted'] is True and loaded[0]['content']==''
    assert capture.WITHDRAWN_AT not in loaded[0]
    again=capture.capture_news_archive(loaded,path,[],now=NOW+timedelta(days=1))
    assert again[0][capture.WITHDRAWN_AT]==withdrawn[0][capture.WITHDRAWN_AT]


def test_initial_capture_load_refuses_unproved_partial_regression(tmp_path):
    path=tmp_path/'capture.json';write(path,[row()]);before=path.read_bytes()
    with pytest.raises(ValueError,match='changed to partial'):
        capture.load_capture_for_aggregation(path,[row(content='New partial',contentComplete=False)],[],now=NOW)
    assert path.read_bytes()==before


def test_actual_initial_load_wires_capture_before_fetch_and_preserves_events(tmp_path):
    path=tmp_path/'capture.json'
    older=row(10,quelleName='Full source',pubDate=(NOW-timedelta(days=20)).isoformat())
    restricted=row(20,quelleName='Restricted source')
    withdrawn=row(30,quelleName='Withdrawn source')
    event=row(40,quelleName='Radar',kontinent='Radar')
    capture.capture_news_archive([older,restricted,withdrawn],path,[],now=NOW,allow_initialize=True)
    capture.capture_news_archive([dict(withdrawn,status='withdrawn')],path,[],now=NOW)
    policies=[{'name':'Restricted source','homepage':'https://source.test/','importMode':'metadata-only'}]
    tree=ast.parse((ROOT/'aggregate.py').read_text())
    def targets(node):
        return {t.id for t in node.targets if isinstance(t,ast.Name)} if isinstance(node,ast.Assign) else set()
    start=next(i for i,n in enumerate(tree.body) if '_capture_rows' in targets(n))
    stop=next(i for i in range(start+1,len(tree.body)) if 'gesehene_titel' in targets(tree.body[i]))
    nodes=tree.body[start:stop+1]
    env={'archiv_dict':{r['link']:r for r in [restricted,withdrawn,event]},
         'quellen':{'Global':[{'name':'Full source'},{'name':'Restricted source'},{'name':'Withdrawn source'}]},
         'read_capture_policies':lambda p:policies,
         'load_capture_for_aggregation':lambda p,rows,pol:capture.load_capture_for_aggregation(path,rows,pol,now=NOW)}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'initial-load','exec'),env)
    actual=env['archiv_dict']
    assert actual[older['link']]['content']==older['content']
    assert actual[restricted['link']]['importMode']=='metadata-only'
    assert actual[withdrawn['link']]['deleted'] is True and actual[withdrawn['link']]['content']==''
    assert actual[event['link']]==event
    assert all(capture.HISTORY not in r and capture.WITHDRAWN_AT not in r for r in actual.values())


def test_checkpoint_publishes_only_sanitized_capture_rows(tmp_path):
    tree=ast.parse((ROOT/'aggregate.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='save_checkpoint')
    path=tmp_path/'capture.json'
    raw=row(kontinent='Global')
    capture.capture_news_archive([raw],path,[],now=NOW,allow_initialize=True)
    outputs={}
    policy=[{'name':'Source','homepage':'https://source.test/','importMode':'metadata-only'}]
    class Clock:
        @staticmethod
        def monotonic():return 10
    env={'time':Clock,'_LAST_CHECKPOINT_AT':0,'CHECKPOINT_INTERVAL_SECONDS':100,
         'archiv_dict':{raw['link']:raw},'date_value':lambda r:1,
         'repair_overbroad_archive_categories':lambda r:r,'ARTICLE_MIN_LENGTHS':{},
         'safe_lower':lambda s:s.lower(),'content_is_incomplete':lambda *a:False,
         'incomplete_limit_for_source':lambda s:5,'read_capture_policies':lambda p:policy,
         'quellen':{'Global':[{'name':'Source'}]},
         'capture_news_archive':lambda rows,p,pol:capture.capture_news_archive(rows,path,pol,now=NOW),
         'public_capture_rows':capture.public_capture_rows,
         'retain_current_sources':lambda rows,names:retain_current_sources(rows,names,now=NOW),
         'atomic_json_write':lambda p,rows:outputs.update({p:rows})}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'checkpoint','exec'),env)
    assert env['save_checkpoint'](True)
    published=outputs['news.json']
    assert len(published)==1 and published[0]['importMode']=='metadata-only'
    assert published[0]['contentComplete'] is False
    assert raw['content'] not in json.dumps(published)
    assert all(capture.HISTORY not in r and capture.WITHDRAWN_AT not in r for r in published)
