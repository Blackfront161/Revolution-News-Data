import unittest,copy,sys,json,tempfile,ast,subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import update_calendar as c
NOW=datetime(2026,11,16,8,tzinfo=timezone.utc)
SOURCE={"id":"test","name":"Test","kind":"gancio","url":"https://example.org","enabled":True}
def event(ident="1",**kwargs):
    raw={"place":{"name":"Venue","address":"1 Explicit Street"}}
    raw.update(kwargs.pop("raw",{}))
    return c.make_event(SOURCE,ident,"Title","https://example.org/event/a",kwargs.pop("start","2026-11-18T19:00:00+01:00"),kwargs.pop("end",""),raw,c.stamp(NOW))
class CalendarTests(unittest.TestCase):
    def test_persisted_reappearance_marker_cannot_override_explicit_cancellation(self):
        active=event();active["eventReinstatedFromSnapshot"]=True
        active["eventRecordUpdatedAt"]="2026-11-17T11:00:00Z"
        dead=event(raw={"status":"cancelled"})
        dead["eventRecordUpdatedAt"]="2026-11-17T10:00:00Z"
        result=c.validate_against_known_tombstones([active],[dead])[0]
        self.assertEqual(result["eventStatus"],"cancelled")
        self.assertGreater(c.parse_instant(result["eventRecordUpdatedAt"]),c.parse_instant(active["eventRecordUpdatedAt"]))
    def test_persisted_reappearance_marker_cannot_override_later_inferred_removal(self):
        active=event();active["eventReinstatedFromSnapshot"]=True
        for checked in ["2026-11-16T08:00:00Z","2026-11-17T08:00:00Z","bad"]:
            active["eventCheckedAt"]=checked
            dead=c.tombstone(event(),NOW+timedelta(days=1),"missing-from-complete-upcoming-snapshot")
            self.assertEqual(c.validate_against_known_tombstones([active],[dead])[0]["eventStatus"],"deleted")
    def test_reappearance_marker_cannot_override_review_expiry(self):
        active=event();active["eventReinstatedFromSnapshot"]=True
        active["eventCheckedAt"]="2026-11-18T08:00:00Z"
        dead=c.tombstone(event(),NOW,"review-validity-expired")
        self.assertEqual(c.validate_against_known_tombstones([active],[dead])[0]["eventStatus"],"deleted")
    def test_publication_is_not_event_start(self):
        with self.assertRaises(ValueError): c.make_event(SOURCE,"1","A","https://example.org/a","",raw={"published":"2026-12-01T10:00:00Z"})
    def test_rejects_offsetless_time(self):
        with self.assertRaises(ValueError):event(start="2026-11-18T19:00:00")
    def test_does_not_invent_end_publication_or_timezone(self):
        r=event()
        self.assertEqual((r["eventEnd"],r["pubDate"],r["eventTimezone"]),("","",""))
        self.assertEqual(r["eventStart"],"2026-11-18T18:00:00Z")
    def test_dst_instants(self):
        a=event(start="2026-10-25T02:30:00+02:00")
        b=event(start="2026-10-25T02:30:00+01:00")
        self.assertNotEqual(a["eventStart"],b["eventStart"])
    def test_bool_not_epoch(self):
        self.assertIsNone(c.parse_instant(True))
    def test_bad_end_rejected(self):
        for end in ["bad","2026-11-17T19:00:00Z"]:
            with self.assertRaises(ValueError):event(end=end)
    def test_long_series_not_continuous(self):
        with self.assertRaises(ValueError):event(end="2027-05-01T20:00:00Z")
    def test_concrete_children_not_expanded(self):
        rows=[{"id":i,"slug":str(i),"title":"Weekly","parentId":3,"start_datetime":int((NOW+timedelta(days=i)).timestamp()),"end_datetime":None} for i in [1,8]]
        result,rejected=c.gancio_events(SOURCE,rows,c.stamp(NOW))
        self.assertEqual(len(result),2);self.assertEqual(rejected,[])
        self.assertNotEqual(result[0]["eventOccurrenceId"],result[1]["eventOccurrenceId"])
        self.assertEqual({r["eventSeriesId"] for r in result},{"test:3"})
        self.assertTrue(all(r["eventRecurrence"]=="" for r in result))
    def test_unknown_status_not_scheduled(self):
        with self.assertRaises(ValueError):event(raw={"status":"mystery"})
    def test_cancellation(self):
        r=event(raw={"status":"cancelled"})
        self.assertTrue(r["cancelled"]);self.assertEqual(r["eventStatus"],"cancelled")
    def test_all_day_no_clock(self):
        r=event(start="2026-11-18",end="2026-11-19",raw={"eventAllDay":True,"timezone":"UTC"})
        self.assertEqual(r["eventStart"],"2026-11-18")
        self.assertEqual(r["eventEndDate"],"2026-11-19")
        self.assertTrue(c.current_event(r,NOW))
        self.assertFalse(c.current_event(r,datetime(2026,11,19,tzinfo=timezone.utc)))
    def test_all_day_bad_end(self):
        with self.assertRaises(ValueError):event(start="2026-11-18",end="2026-11-18",raw={"eventAllDay":True})
    def test_failed_snapshot_preserves_last_good(self):
        old=event()
        self.assertEqual(c.merge_source([old],[],False,NOW),[old])
    def test_complete_absence_is_deletion_not_cancellation(self):
        r=c.merge_source([event()],[],True,NOW)[0]
        self.assertEqual(r["eventStatus"],"deleted");self.assertFalse(r["cancelled"])
    def test_updated_start_replaces_same_identity(self):
        old=event();new=event(start="2026-11-19T20:00:00Z")
        rows=c.merge_source([old],[new],True,NOW)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["eventOccurrenceId"],old["eventOccurrenceId"])
        self.assertEqual(rows[0]["eventStart"],new["eventStart"])
    def test_same_url_distinct_occurrences_keep_both(self):
        a=event("1");b=event("2",start="2026-11-19T19:00:00Z")
        self.assertEqual(len(c.deduplicate([a,b])),2)
    def test_federated_exact_duplicate_merges(self):
        a=event();b=event("2");b["eventSourceId"]="another"
        rows=c.deduplicate([a,b])
        self.assertEqual(len(rows),1);self.assertEqual(len(rows[0]["eventAliases"]),2)
    def test_tombstone_wins_over_active_duplicate(self):
        a=event();b=c.tombstone(event("2"),NOW,"test");b["eventSourceId"]="other"
        self.assertEqual(c.deduplicate([a,b])[0]["eventStatus"],"deleted")
        self.assertEqual(c.deduplicate([b,a])[0]["eventStatus"],"deleted")
    def test_no_global_title_only_dedup(self):
        a=event();b=event("2");b["eventAddress"]=""
        self.assertEqual(len(c.deduplicate([a,b])),2)
    def test_legacy_unverified_rejected(self):
        self.assertFalse(c.current_event({"eventStart":"2026-12-01T00:00:00Z"},NOW))
    def test_old_start_without_end_not_ongoing_forever(self):
        self.assertFalse(c.current_event(event(start="2026-10-01T10:00:00Z"),NOW))
    def test_expired_tombstone_removed(self):
        r=c.tombstone(event(start="2026-10-01T10:00:00Z"),NOW-timedelta(days=31),"test")
        self.assertFalse(c.current_event(r,NOW))
    def test_ikuwo_machine_time_not_publication(self):
        body='<div class="event_item status-scheduled"><a href="https://ikuwo.de/veranstaltung/a/"><h4>A</h5></a><div><time itemprop="dtstart" datetime="2026-11-18T20:30:00+01:00">Text</time></div></div>'
        rows,rejected=c.ikuwo_events(SOURCE,body,c.stamp(NOW))
        self.assertEqual(rows[0]["eventStart"],"2026-11-18T19:30:00Z")
        self.assertEqual(rows[0]["eventEnd"],"")
    def test_radar_rrule_does_not_invent_occurrences(self):
        raw={"result":{"1":{"title":"Weekly","date_time":[{"value":1795000000,"value2":1800000000,"rrule":"FREQ=WEEKLY;COUNT=6"}]}}}
        rows,rejected=c.radar_events(SOURCE,raw,c.stamp(NOW))
        self.assertEqual(rows,[]);self.assertEqual(len(rejected),1)
    def test_publisher_updated_not_fetch_date(self):
        r=event(raw={"updatedAt":"2026-11-01T10:00:00Z"})
        self.assertEqual(r["updatedAt"],"2026-11-01T10:00:00Z")
        self.assertEqual(r["eventCheckedAt"],c.stamp(NOW))
    def test_all_failed_has_no_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE]}))
            old=b'[{"sentinel":true}]';(p/"events-v2.json").write_bytes(old)
            with patch.object(c,"collect",return_value=([],{"state":"failed","complete":False})):
                with self.assertRaises(RuntimeError):c.refresh(p,NOW)
            self.assertEqual((p/"events-v2.json").read_bytes(),old)
            self.assertFalse((p/"events-v2-feed.json").exists())
    def test_news_files_not_changed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE]}))
            (p/"news.json").write_bytes(b'[{"news":"untouched"}]')
            (p/"news-feed.json").write_bytes(b'[{"news":"small"}]')
            before={n:(p/n).read_bytes() for n in ["news.json","news-feed.json"]}
            with patch.object(c,"collect",return_value=([event()],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            self.assertEqual(before,{n:(p/n).read_bytes() for n in before})

    def test_missing_native_identity_rejected(self):
        with self.assertRaises(ValueError):event(None)
    def test_explicit_cancellation_not_undone_by_later_fetch(self):
        old=event(raw={"status":"cancelled"});new=event()
        new["eventCheckedAt"]=c.stamp(NOW+timedelta(hours=1))
        self.assertEqual(c.merge_source([old],[new],True,NOW)[0]["eventStatus"],"cancelled")
    def test_later_publisher_revision_can_reinstate(self):
        old=event(raw={"status":"cancelled","updatedAt":"2026-11-14T10:00:00Z"})
        new=event(raw={"status":"scheduled","updatedAt":"2026-11-15T10:00:00Z"})
        self.assertEqual(c.merge_source([old],[new],True,NOW)[0]["eventStatus"],"scheduled")
    def test_tied_publisher_revisions_favour_cancellation(self):
        old=event(raw={"status":"cancelled","updatedAt":"2026-11-14T10:00:00Z"})
        new=event(raw={"status":"scheduled","updatedAt":"2026-11-14T10:00:00Z"})
        for rows in [[old,new],[new,old]]:
            self.assertEqual(c.deduplicate(rows)[0]["eventStatus"],"cancelled")
    def test_inferred_deletion_reappearance_needs_later_check(self):
        old=c.tombstone(event(),NOW,"missing-from-complete-upcoming-snapshot")
        new=event();new["eventCheckedAt"]=c.stamp(NOW+timedelta(hours=1))
        restored=c.merge_source([old],[new],True,NOW)[0]
        self.assertEqual(restored["eventStatus"],"scheduled")
        self.assertTrue(restored["eventReinstatedFromSnapshot"])
    def test_ap_and_plain_duplicate_merge(self):
        a=event();a["eventCanonicalOrigin"]="https://origin.example/event/a"
        b=event("2");b["eventSourceId"]="other"
        self.assertEqual(len(c.deduplicate([a,b])),1)
    def test_radar_multidate_array_position_not_identity(self):
        raw={"result":{"1":{"title":"Series","date_time":[{"value":1795000000},{"value":1796000000}]}}}
        rows,rejected=c.radar_events(SOURCE,raw,c.stamp(NOW))
        self.assertEqual(rows,[]);self.assertEqual(len(rejected),1)
    def test_all_day_known_zone(self):
        r=event(start="2026-11-18",end="2026-11-19",raw={"eventAllDay":True,"timezone":"America/Los_Angeles"})
        self.assertTrue(c.current_event(r,datetime(2026,11,19,1,tzinfo=timezone.utc)))
        self.assertFalse(c.current_event(r,datetime(2026,11,19,9,tzinfo=timezone.utc)))
    def test_postponement_not_labelled_cancellation(self):
        with self.assertRaises(ValueError):event(raw={"status":"postponed"})
    def test_zinn_requires_same_year(self):
        with self.assertRaises(ValueError):
            c.zinn_events(SOURCE,"December 6, 2026 CCSF Mission Campus 1125 Valencia","<title>2025 Panels</title>",c.stamp(NOW))
    def test_feed_status_news_metadata_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE]}))
            before={"news":{"revision":"news-original","lastSuccessfulFetchAt":"old"},"aggregation":{"mode":"fast"},"lastSuccessfulFetchAt":"news-original"}
            (p/"feed-status.json").write_text(json.dumps(before))
            with patch.object(c,"collect",return_value=([event()],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            after=json.loads((p/"feed-status.json").read_text())
            self.assertEqual({k:after[k] for k in before},before)
            self.assertTrue(after["events"]["revision"])

    def test_unchanged_recheck_preserves_material_revision(self):
        old=event()
        new=event();new["eventCheckedAt"]=c.stamp(NOW+timedelta(hours=1));new["eventRecordUpdatedAt"]=new["eventCheckedAt"];new["calendarGenerationAt"]=new["eventCheckedAt"]
        row=c.merge_source([old],[new],True,NOW)[0]
        self.assertEqual(row["eventRecordUpdatedAt"],old["eventRecordUpdatedAt"])
        self.assertEqual(row["eventCheckedAt"],new["eventCheckedAt"])
    def test_cancellation_recheck_preserves_material_revision(self):
        old=event(raw={"status":"cancelled"})
        new=event(raw={"status":"cancelled"});new["eventCheckedAt"]=c.stamp(NOW+timedelta(hours=1));new["eventRecordUpdatedAt"]=new["eventCheckedAt"]
        self.assertEqual(c.merge_source([old],[new],True,NOW)[0]["eventRecordUpdatedAt"],old["eventRecordUpdatedAt"])
    def test_future_tombstone_not_expired_after_thirty_days(self):
        old=c.tombstone(event(),NOW-timedelta(days=31),"test")
        self.assertTrue(c.current_event(old,NOW))
    def test_per_source_cache_survives_federation_dedup(self):
        other={**SOURCE,"id":"other"}
        a=event();b=event();b["id"]=b["eventOccurrenceId"]=b["eventUuid"]=b["eventApiId"]="other:1";b["eventSourceId"]="other";b["eventAliases"]=["other:1"]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE,other]}))
            def fake(source,*args):return ([a] if source["id"]=="test" else [b]),{"sourceId":source["id"],"state":"ok","complete":True}
            with patch.object(c,"collect",side_effect=fake):c.refresh(p,NOW)
            cache=json.loads((p/"calendar-source-cache.json").read_text())
            self.assertEqual(set(cache["sources"]),{"test","other"})
            self.assertEqual(len(json.loads((p/"events-v2.json").read_text())),1)

    def test_news_checkpoint_never_writes_calendar(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/"aggregate.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="atomic_json_write" and node.args and isinstance(node.args[0],ast.Constant):
                self.assertNotIn(node.args[0].value,["events.json","events-feed.json","events-v2.json","events-v2-feed.json","calendar-status.json","calendar-source-cache.json"])
    def test_legacy_normalizer_never_guesses_date(self):
        source=(Path(__file__).resolve().parents[1]/"aggregate.py").read_text()
        tree=ast.parse(source);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="normalize_feed_event")
        import re
        context={"safe_text":lambda value,default="":value or default,"GANCIO_EVENT_DATE_RE":re.compile(r"^\[\d{4}-\d{2}-\d{2}\]\s*")}
        exec(compile(ast.Module(body=[function],type_ignores=[]),"<normalizer>","exec"),context)
        self.assertEqual(context["normalize_feed_event"]("No event date","2026-12-01T10:00:00Z")[1],"")
        self.assertEqual(context["normalize_feed_event"]("[2026-12-01] Date only","2026-11-01T10:00:00Z")[1],"")
    def test_calendar_job_shares_writer_group_and_needs_no_paid_service(self):
        workflow=(Path(__file__).resolve().parents[1]/".github/workflows/update-calendar.yml").read_text(encoding="utf-8-sig")
        self.assertIn('cron: "23 * * * *"',workflow)
        self.assertIn("group: wrn-main-write",workflow)
        self.assertIn("ref: main",workflow)
        self.assertNotIn("upload-artifact",workflow)
        self.assertNotIn("secrets.",workflow)

    def test_material_active_revision_overrides_older_dead_despite_publisher_order(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-16T07:00:00Z"})
        active=event(raw={"status":"scheduled","updatedAt":"2026-11-15T07:00:00Z"})
        active["eventRecordUpdatedAt"]=c.stamp(NOW+timedelta(hours=1))
        for a,b in [(dead,active),(active,dead)]:
            self.assertIs(c.preferred_record(a,b),active)
    def test_material_dead_revision_overrides_older_active_despite_publisher_order(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-14T07:00:00Z"})
        active=event(raw={"status":"scheduled","updatedAt":"2026-11-15T07:00:00Z"})
        dead["eventRecordUpdatedAt"]=c.stamp(NOW+timedelta(hours=1))
        for a,b in [(dead,active),(active,dead)]:
            self.assertIs(c.preferred_record(a,b),dead)
    def test_equal_material_revision_dead_wins_even_if_active_publisher_newer(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-14T07:00:00Z"})
        active=event(raw={"status":"scheduled","updatedAt":"2026-11-15T07:00:00Z"})
        self.assertIs(c.preferred_record(dead,active),dead)
        self.assertIs(c.preferred_record(active,dead),dead)
    def test_publisher_fallback_only_when_material_revision_missing(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-14T07:00:00Z"})
        active=event(raw={"status":"scheduled","updatedAt":"2026-11-15T07:00:00Z"})
        del dead["eventRecordUpdatedAt"];del active["eventRecordUpdatedAt"]
        self.assertIs(c.preferred_record(dead,active),active)
    def test_new_federated_alias_cannot_bypass_known_cancellation(self):
        dead=event(raw={"status":"cancelled"})
        active=event("another");active["eventSourceId"]="other";active["eventRecordUpdatedAt"]=c.stamp(NOW+timedelta(hours=1))
        union=c.validate_against_known_tombstones([active],[dead])
        self.assertEqual(union[0]["eventStatus"],"cancelled")
    def test_semantic_changes_get_strictly_later_material_revision(self):
        old=event();new=event(start="2026-11-19T19:00:00Z")
        result=c.merge_source([old],[new],True,NOW)[0]
        self.assertGreater(c.parse_instant(result["eventRecordUpdatedAt"]),c.parse_instant(old["eventRecordUpdatedAt"]))

    def test_replay_parser_rejection_never_claims_complete_or_deletes_old(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);data=json.dumps([{"id":1,"title":"No explicit time","slug":"bad"}]).encode()
            (p/"source.json").write_bytes(data)
            (p/"gancio-api-health.json").write_text(json.dumps([{"baseUrl":SOURCE["url"],"rawFile":"source.json","sha256":hashlib.sha256(data).hexdigest(),"checkedAt":c.stamp(NOW)}]))
            rows,status=c.collect(SOURCE,NOW,replay=p)
            self.assertEqual(rows,[]);self.assertEqual(len(status["rejected"]),1)
            self.assertFalse(status["complete"]);self.assertEqual(status["state"],"partial")
            self.assertEqual(c.merge_source([event()],rows,status["complete"],NOW),[event()])
    def test_current_batch_new_cancellation_blocks_stale_later_captured_alias(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-15T10:00:00Z"})
        active=event("copy",raw={"status":"scheduled","updatedAt":"2026-11-14T10:00:00Z"})
        active["eventSourceId"]="copy";active["eventRecordUpdatedAt"]=c.stamp(NOW+timedelta(minutes=1))
        for row in [dead,active]:row["eventCanonicalOrigin"]="https://origin.example/event/1"
        for rows in [[dead,active],[active,dead]]:
            result=c.deduplicate(c.validate_against_known_tombstones(rows,[]))
            self.assertEqual(len(result),1);self.assertEqual(result[0]["eventStatus"],"cancelled")
    def test_current_batch_later_publisher_reinstates_even_if_dead_captured_later(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-14T10:00:00Z"})
        active=event("copy",raw={"status":"scheduled","updatedAt":"2026-11-15T10:00:00Z"})
        dead["eventRecordUpdatedAt"]=c.stamp(NOW+timedelta(minutes=1))
        for row in [dead,active]:row["eventCanonicalOrigin"]="https://origin.example/event/1"
        for rows in [[dead,active],[active,dead]]:
            result=c.deduplicate(c.validate_against_known_tombstones(rows,[]))
            self.assertEqual(result[0]["eventStatus"],"scheduled")
            self.assertGreater(c.parse_instant(result[0]["eventRecordUpdatedAt"]),c.parse_instant(dead["eventRecordUpdatedAt"]))
    def _seed_transaction(self,p):
        (p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE]}))
        (p/"feed-status.json").write_text(json.dumps({"news":{"revision":"keep-news"},"events":{}}))
        (p/"news.json").write_bytes(b'[{"news":"old"}]')
        with patch.object(c,"collect",return_value=([event()],{"sourceId":"test","state":"ok","complete":True})):
            c.refresh(p,NOW)
        return {name:(p/name).read_bytes() for name in c.CALENDAR_OUTPUTS}
    def test_every_output_write_exception_before_and_after_rolls_back_and_news_continues(self):
        cases=0
        for selected in c.CALENDAR_OUTPUTS:
            for phase in ["before","after"]:
                with self.subTest(file=selected,phase=phase),tempfile.TemporaryDirectory() as d:
                    p=Path(d);before=self._seed_transaction(p);real=c.install_calendar_file;fired=[False]
                    def fault(path,data):
                        hit=path.name==selected and not fired[0]
                        if hit and phase=="before":fired[0]=True;raise OSError("injected before output write")
                        real(path,data)
                        if hit and phase=="after":fired[0]=True;raise OSError("injected after output write")
                    with patch.object(c,"collect",return_value=([event(start="2026-11-19T19:00:00Z")],{"sourceId":"test","state":"ok","complete":True})),patch.object(c,"install_calendar_file",side_effect=fault):
                        with self.assertRaises(OSError):c.refresh(p,NOW)
                    self.assertTrue(fired[0]);self.assertFalse((p/c.JOURNAL).exists())
                    self.assertEqual(before,{name:(p/name).read_bytes() for name in c.CALENDAR_OUTPUTS})
                    self.assertEqual(len(json.loads((p/"events-v2.json").read_text())),1)
                    c.guard_before_news_commit(p)
                    (p/"news.json").write_bytes(b'[{"news":"new"}]')
                    self.assertEqual((p/"news.json").read_bytes(),b'[{"news":"new"}]')
                    cases+=1
        self.assertEqual(cases,len(c.CALENDAR_OUTPUTS)*2)
    def test_every_output_hard_interruption_before_and_after_is_recovered_before_news(self):
        class ProcessInterrupted(BaseException):pass
        cases=0
        for selected in c.CALENDAR_OUTPUTS:
            for phase in ["before","after"]:
                with self.subTest(file=selected,phase=phase),tempfile.TemporaryDirectory() as d:
                    p=Path(d);before=self._seed_transaction(p);real=c.install_calendar_file
                    def crash(path,data):
                        if path.name==selected and phase=="before":raise ProcessInterrupted()
                        real(path,data)
                        if path.name==selected and phase=="after":raise ProcessInterrupted()
                    with patch.object(c,"collect",return_value=([event(start="2026-11-19T19:00:00Z")],{"sourceId":"test","state":"ok","complete":True})),patch.object(c,"install_calendar_file",side_effect=crash):
                        with self.assertRaises(ProcessInterrupted):c.refresh(p,NOW)
                    self.assertTrue((p/c.JOURNAL).exists())
                    with self.assertRaises(RuntimeError):c.verify_calendar_generation(p)
                    c.guard_before_news_commit(p)
                    self.assertFalse((p/c.JOURNAL).exists())
                    self.assertEqual(before,{name:(p/name).read_bytes() for name in c.CALENDAR_OUTPUTS})
                    (p/"news.json").write_bytes(b'[{"news":"continues"}]')
                    self.assertTrue((p/"news.json").exists());cases+=1
        self.assertEqual(cases,len(c.CALENDAR_OUTPUTS)*2)
    def test_equal_count_mixed_generation_is_rejected_by_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            rows=json.loads((p/"events-v2.json").read_text())
            self.assertEqual(len(rows),1);rows[0]["title"]="Different generation, same count"
            (p/"events-v2.json").write_text(json.dumps(rows))
            with self.assertRaises(ValueError):c.verify_calendar_generation(p)
    def test_news_workflow_recovers_before_builder_and_verifies_before_staging(self):
        s=(Path(__file__).resolve().parents[1]/".github/workflows/update.yml").read_text()
        self.assertLess(s.index("--recover-only"),s.index('WRN_FEED_TARGETS="news,status"'))
        self.assertLess(s.index("--verify-generation"),s.index("git add news.json"))
        self.assertIn("continue-on-error: true",s)

    def test_real_process_exit_each_write_recovers_exact_generation_and_news_continues(self):
        child = """
import sys,os,json
from pathlib import Path
from datetime import datetime,timezone
import update_calendar as c
root=Path(sys.argv[1]);selected=sys.argv[2];phase=sys.argv[3]
now=datetime(2026,11,16,8,tzinfo=timezone.utc)
source={"id":"test","name":"Test","kind":"gancio","url":"https://example.org","enabled":True}
row=c.make_event(source,"1","Changed","https://example.org/event/a","2026-11-19T19:00:00Z",raw={"place":{"name":"Venue","address":"1 Explicit Street"}},checked=c.stamp(now))
c.collect=lambda *args:([row],{"sourceId":"test","state":"ok","complete":True})
real=c.install_calendar_file
def crash(path,data):
 if path.name==selected and phase=="before":os._exit(73)
 real(path,data)
 if path.name==selected and phase=="after":os._exit(73)
c.install_calendar_file=crash
c.refresh(root,now)
"""
        module_root=Path(__file__).resolve().parents[1]
        cases=0
        for selected in c.CALENDAR_OUTPUTS:
            for phase in ["before","after"]:
                with self.subTest(file=selected,phase=phase),tempfile.TemporaryDirectory() as d:
                    p=Path(d);before=self._seed_transaction(p)
                    crashed=subprocess.run([sys.executable,"-B","-c",child,str(p),selected,phase],cwd=module_root,capture_output=True)
                    self.assertEqual(crashed.returncode,73,crashed.stderr)
                    self.assertTrue((p/c.JOURNAL).exists())
                    with self.assertRaises(RuntimeError):c.verify_calendar_generation(p)
                    recovered=subprocess.run([sys.executable,"-B",str(module_root/"update_calendar.py"),"--root",str(p),"--recover-only"],cwd=module_root,capture_output=True)
                    self.assertEqual(recovered.returncode,0,recovered.stderr)
                    self.assertEqual(before,{name:(p/name).read_bytes() for name in c.CALENDAR_OUTPUTS})
                    c.verify_calendar_generation(p)
                    (p/"news.json").write_bytes(b'[{"news":"continues after actual process exit"}]')
                    self.assertIn(b"continues",(p/"news.json").read_bytes())
                    cases+=1
        self.assertEqual(cases,len(c.CALENDAR_OUTPUTS)*2)

    def test_same_count_same_revision_wrong_status_timestamp_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            state=json.loads((p/"feed-status.json").read_text())
            state["events"]["lastSuccessfulFetchAt"]="2000-01-01T00:00:00Z"
            (p/"feed-status.json").write_text(json.dumps(state))
            with self.assertRaises(ValueError):c.verify_calendar_generation(p)
    def test_local_git_news_commit_after_calendar_failure_has_no_partial_calendar(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);before=self._seed_transaction(p)
            def git(*args):
                r=subprocess.run(["git",*args],cwd=p,capture_output=True)
                self.assertEqual(r.returncode,0,r.stderr)
                return r.stdout
            git("init","-q");git("config","user.name","Calendar Transaction Test");git("config","user.email","test@example.invalid")
            git("add",".");git("commit","-q","-m","Baseline")
            real=c.install_calendar_file;fired=[False]
            def fail_after_feed(path,data):
                real(path,data)
                if path.name=="events-feed.json" and not fired[0]:
                    fired[0]=True;raise OSError("injected partial generation")
            with patch.object(c,"collect",return_value=([event(start="2026-11-19T19:00:00Z")],{"sourceId":"test","state":"ok","complete":True})),patch.object(c,"install_calendar_file",side_effect=fail_after_feed):
                with self.assertRaises(OSError):c.refresh(p,NOW)
            c.guard_before_news_commit(p)
            (p/"news.json").write_bytes(b'[{"news":"new"}]')
            state=json.loads((p/"feed-status.json").read_text());state["news"]["revision"]="new-news"
            (p/"feed-status.json").write_text(json.dumps(state))
            c.verify_calendar_generation(p)
            git("add","news.json",*c.CALENDAR_OUTPUTS)
            staged=set(git("diff","--cached","--name-only").decode().splitlines())
            self.assertEqual(staged,{"news.json","feed-status.json"})
            git("commit","-q","-m","Publish news after recovered calendar failure")
            for name,data in before.items():
                if name!="feed-status.json":self.assertEqual(git("show","HEAD:"+name),data)

    def test_distinct_native_ids_within_same_source_are_not_heuristically_collapsed(self):
        a=event("1");b=event("2")
        self.assertEqual(len(c.deduplicate([a,b])),2)
    def test_new_native_id_does_not_inherit_same_source_missing_id_deletion(self):
        dead=c.tombstone(event("old"),NOW,"missing-from-complete-upcoming-snapshot")
        new=event("new")
        result=c.deduplicate(c.validate_against_known_tombstones([dead,new],[dead]))
        self.assertEqual({r["eventOccurrenceId"]:r["eventStatus"] for r in result},{"test:old":"deleted","test:new":"scheduled"})
    def test_valid_cancellation_of_last_active_event_is_published(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            with patch.object(c,"collect",return_value=([event(raw={"status":"cancelled"})],{"sourceId":"test","state":"ok","complete":True})):
                status=c.refresh(p,NOW)
            self.assertEqual(status["scheduledCount"],0)
            self.assertEqual(json.loads((p/"events-v2-feed.json").read_text())[0]["eventStatus"],"cancelled")
            c.verify_calendar_generation(p)
    def test_complete_removal_of_last_active_event_is_published(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            with patch.object(c,"collect",return_value=([],{"sourceId":"test","state":"ok","complete":True})):
                status=c.refresh(p,NOW)
            self.assertEqual(status["scheduledCount"],0)
            self.assertEqual(json.loads((p/"events-v2-feed.json").read_text())[0]["eventStatus"],"deleted")
            c.verify_calendar_generation(p)

    def test_material_revision_millisecond_boundaries_and_carry(self):
        cases=[
          ("2026-11-16T08:00:00.000001Z","2026-11-16T08:00:00.000999Z","2026-11-16T08:00:00.001Z"),
          ("2026-11-16T08:00:00.000999Z","2026-11-16T08:00:00.001000Z","2026-11-16T08:00:00.001Z"),
          ("2026-11-16T08:00:00.999999Z","2026-11-16T08:00:00.999999Z","2026-11-16T08:00:01.000Z"),
          ("2026-11-16T23:59:59.999999Z","2026-11-16T23:59:59.999999Z","2026-11-17T00:00:00.000Z"),
          ("2026-11-16T08:00:00.005Z","2026-11-16T07:59:59.999999Z","2026-11-16T08:00:00.006Z")]
        for old,new,expected in cases:
            with self.subTest(old=old,new=new):self.assertEqual(c.next_material_revision(old,new),expected)
    def test_material_same_millisecond_semantic_change_advances_full_millisecond(self):
        old=event();old["eventRecordUpdatedAt"]="2026-11-16T08:00:00.000001Z"
        new=event();new["title"]="Changed";new["eventRecordUpdatedAt"]="2026-11-16T08:00:00.000999Z"
        row=c.merge_source([old],[new],True,NOW)[0]
        self.assertEqual(row["eventRecordUpdatedAt"],"2026-11-16T08:00:00.001Z")
    def test_publisher_microsecond_value_is_not_rewritten(self):
        value="2026-11-15T10:00:00.000123Z"
        row=event(raw={"updatedAt":value})
        self.assertEqual(row["eventUpdated"],value)
        self.assertEqual(row["updatedAt"],value)
        self.assertRegex(row["eventRecordUpdatedAt"],r"\.\d{3}Z$")
    def test_unchanged_normalized_recheck_material_bytes_stay_identical(self):
        old=event();new=event();new["eventCheckedAt"]="2026-11-16T08:00:00.000999Z"
        row=c.merge_source([old],[new],True,NOW)[0]
        self.assertEqual(row["eventRecordUpdatedAt"].encode(),old["eventRecordUpdatedAt"].encode())
    def test_legacy_microsecond_material_tie_matches_js_resolution(self):
        dead=event(raw={"status":"cancelled"});active=event()
        dead["eventRecordUpdatedAt"]="2026-11-16T08:00:00.000001Z"
        active["eventRecordUpdatedAt"]="2026-11-16T08:00:00.000999Z"
        self.assertIs(c.preferred_record(dead,active),dead)
        self.assertIs(c.preferred_record(active,dead),dead)
    def test_publisher_fallback_submillisecond_tie_remains_cancelled(self):
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-15T10:00:00.000001Z"})
        active=event(raw={"status":"scheduled","updatedAt":"2026-11-15T10:00:00.000999Z"})
        del dead["eventRecordUpdatedAt"];del active["eventRecordUpdatedAt"]
        self.assertIs(c.preferred_record(dead,active),dead)
    def test_verified_alias_group_material_revision_persists_after_rescan(self):
        other={**SOURCE,"id":"other"}
        dead=event(raw={"status":"cancelled","updatedAt":"2026-11-14T10:00:00Z"})
        active=c.make_event(other,"1","Title","https://example.org/event/a","2026-11-18T19:00:00+01:00",raw={"status":"scheduled","updatedAt":"2026-11-13T10:00:00Z","place":{"name":"Venue","address":"1 Explicit Street"}},checked="2026-11-16T08:00:00.000999Z")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"calendar-sources.json").write_text(json.dumps({"sources":[SOURCE,other]}))
            def collect(source,*args):return ([copy.deepcopy(dead)] if source["id"]=="test" else [copy.deepcopy(active)]),{"sourceId":source["id"],"state":"ok","complete":True}
            with patch.object(c,"collect",side_effect=collect):c.refresh(p,NOW)
            first=json.loads((p/"events-v2.json").read_text())[0]
            self.assertEqual(first["eventStatus"],"cancelled")
            self.assertGreater(c.material_instant(first["eventRecordUpdatedAt"]),c.material_instant(active["eventRecordUpdatedAt"]))
            with patch.object(c,"collect",side_effect=collect):c.refresh(p,NOW)
            second=json.loads((p/"events-v2.json").read_text())[0]
            self.assertEqual(first["eventRecordUpdatedAt"],second["eventRecordUpdatedAt"])
            self.assertEqual(set(second["eventAliases"]),{"test:1","other:1"})
    def test_calendar_push_paths_trigger_code_not_data_self_commits(self):
        import fnmatch
        source=(Path(__file__).resolve().parents[1]/".github/workflows/update-calendar.yml").read_text()
        section=source[source.index("  push:"):source.index("  schedule:")]
        self.assertIn("      - main",section)
        declared=[line.strip()[2:] for line in section.splitlines() if line.strip().startswith("- ") and line.strip()!="- main"]
        self.assertEqual(set(declared),{"update_calendar.py","calendar-sources.json",".github/workflows/update-calendar.yml"})
        self.assertFalse(any(fnmatch.fnmatch(output,pattern) for output in c.CALENDAR_OUTPUTS for pattern in declared))

    def test_legacy_routes_exclude_cancellation_but_v2_retains_full_tombstone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            dead=event(raw={"status":"cancelled","updatedAt":"2026-11-15T10:00:00Z"})
            with patch.object(c,"collect",return_value=([dead],{"sourceId":"test","state":"ok","complete":True})):
                state=c.refresh(p,NOW)
            self.assertEqual(json.loads((p/"events.json").read_text()),[])
            self.assertEqual(json.loads((p/"events-feed.json").read_text()),[])
            full=json.loads((p/"events-v2.json").read_text())
            self.assertEqual(full[0]["eventStatus"],"cancelled")
            self.assertEqual(full[0]["eventStart"],dead["eventStart"])
            status=json.loads((p/"feed-status.json").read_text())
            self.assertEqual(status["events"]["archiveCount"],0)
            self.assertEqual(status["events"]["feedCount"],0)
            self.assertEqual(status["calendarV2"]["archiveCount"],1)
            self.assertEqual(status["calendarV2"]["feedCount"],1)
            c.verify_calendar_generation(p)
    def test_legacy_routes_exclude_deleted_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            with patch.object(c,"collect",return_value=([],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            self.assertEqual(json.loads((p/"events.json").read_text()),[])
            self.assertEqual(json.loads((p/"events-v2-feed.json").read_text())[0]["eventStatus"],"deleted")
    def test_both_route_generations_and_status_sections_are_hash_bound(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            marker=json.loads((p/"calendar-generation.json").read_text())
            self.assertEqual(set(marker["files"]),{"calendar-source-cache.json","events-v2.json","events-v2-feed.json","events.json","events-feed.json","calendar-status.json"})
            status=json.loads((p/"feed-status.json").read_text())
            status["calendarV2"]["lastSuccessfulFetchAt"]="2000-01-01T00:00:00Z"
            (p/"feed-status.json").write_text(json.dumps(status))
            with self.assertRaises(ValueError):c.verify_calendar_generation(p)
    def test_v2_previous_tombstone_survives_source_cache_loss_and_stale_active_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            dead=event(raw={"status":"cancelled","updatedAt":"2026-11-15T10:00:00Z"})
            with patch.object(c,"collect",return_value=([dead],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            previous=json.loads((p/"events-v2.json").read_text())[0]
            (p/"calendar-source-cache.json").unlink()
            stale=event(raw={"status":"scheduled","updatedAt":"2026-11-14T10:00:00Z"})
            with patch.object(c,"collect",return_value=([stale],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            row=json.loads((p/"events-v2.json").read_text())[0]
            self.assertEqual(row["eventStatus"],"cancelled")
            self.assertEqual(row["eventRecordUpdatedAt"],previous["eventRecordUpdatedAt"])
            self.assertEqual(row["eventAliases"],previous["eventAliases"])
            self.assertEqual(row["eventStart"],previous["eventStart"])
            self.assertEqual(json.loads((p/"events.json").read_text()),[])
    def test_legacy_default_feed_builder_cannot_emit_tombstones(self):
        from build_web_feeds import prepare_events
        future=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
        active=event("active",start=future)
        dead=event("dead",start=future,raw={"status":"cancelled"})
        deleted=c.tombstone(event("deleted",start=future),datetime.now(timezone.utc),"test")
        rows=prepare_events([active,dead,deleted],limit=1000,content_limit=2800)
        self.assertEqual([r["eventOccurrenceId"] for r in rows],[active["eventOccurrenceId"]])
    def test_status_builder_keeps_v2_section_without_touching_news_metadata(self):
        from build_web_feeds import calendar_status_sections
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            status=json.loads((p/"calendar-status.json").read_text())
            sections=calendar_status_sections(status,(p/"events-feed.json").stat().st_size,(p/"events-v2-feed.json").stat().st_size)
            stored=json.loads((p/"feed-status.json").read_text())
            self.assertEqual(sections["events"],stored["events"])
            self.assertEqual(sections["calendarV2"],stored["calendarV2"])
            self.assertEqual(stored["news"]["revision"],"keep-news")
    def test_v2_previous_route_prevents_legacy_active_projection_from_losing_alias_cancellation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self._seed_transaction(p)
            dead=event(raw={"status":"cancelled","updatedAt":"2026-11-15T10:00:00Z"})
            dead["eventAliases"]=["test:1","remote:9"]
            with patch.object(c,"collect",return_value=([dead],{"sourceId":"test","state":"ok","complete":True})):
                c.refresh(p,NOW)
            (p/"calendar-source-cache.json").unlink()
            with patch.object(c,"collect",return_value=([],{"sourceId":"test","state":"partial","complete":False})):
                c.refresh(p,NOW)
            previous=json.loads((p/"events-v2.json").read_text())[0]
            self.assertEqual(set(previous["eventAliases"]),{"test:1","remote:9"})
            self.assertEqual(previous["eventStatus"],"cancelled")
            self.assertTrue(c.current_event(previous,NOW))
if __name__=="__main__":unittest.main()
