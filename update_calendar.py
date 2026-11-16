#!/usr/bin/env python3
"""Dedicated structured calendar writer. No imports or writes to the news pipeline."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, html, json, os, re, tempfile, shutil, subprocess
import urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

UTC=timezone.utc
MAX_BYTES=8_000_000
MAX_PAGES=20
PAGE_SIZE=500
DAYS=120
TOMBSTONE_DAYS=30

def stamp(value=None):
    return (value or datetime.now(UTC)).isoformat().replace("+00:00","Z")

def parse_instant(value):
    if isinstance(value,bool) or value is None or value=="": return None
    try:
        if isinstance(value,(int,float)) or (isinstance(value,str) and value.isdigit()):
            dt=datetime.fromtimestamp(float(value),UTC)
        else:
            dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if dt.tzinfo is None: return None
        return dt.astimezone(UTC)
    except (ValueError,TypeError,OverflowError,OSError): return None

def text(value):
    if value is None: return ""
    return html.unescape(re.sub("<[^>]+>"," ",str(value))).strip()

def norm(value): return re.sub(r"\s+"," ",text(value)).casefold().strip()

def safe_url(value):
    s=str(value or "").strip()
    try:
        p=urllib.parse.urlsplit(s)
        if p.scheme=="https" and p.netloc and not p.username and not p.password: return s
    except ValueError: pass
    return ""

def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    handle,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(handle,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.write("\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


CALENDAR_OUTPUTS=("calendar-source-cache.json","events.json","events-feed.json","calendar-status.json","feed-status.json","calendar-generation.json")
JOURNAL=".calendar-transaction.json"

def byte_hash(data):return hashlib.sha256(data).hexdigest()

def json_bytes(data):
    return (json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

def install_calendar_file(path,data):
    handle,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(handle,"wb") as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def recover_calendar_transaction(root):
    journal_path=root/JOURNAL
    if not journal_path.exists():return False
    journal=json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("schema")!="wrn.calendar-transaction.v1":raise ValueError("Invalid calendar recovery journal")
    backup=root/journal["backupDirectory"]
    if backup.parent.resolve()!=root.resolve() or not backup.name.startswith(".calendar-backup-"):
        raise ValueError("Calendar backup outside output root")
    for name,entry in journal["previous"].items():
        if name not in CALENDAR_OUTPUTS:raise ValueError("Unexpected recovery path")
        target=root/name
        if entry["existed"]:
            data=(backup/name).read_bytes()
            if byte_hash(data)!=entry["sha256"]:raise ValueError("Calendar backup hash mismatch")
            install_calendar_file(target,data)
        elif target.exists():target.unlink()
    journal_path.unlink()
    shutil.rmtree(backup)
    return True

def commit_calendar_generation(root,outputs):
    if any(name not in CALENDAR_OUTPUTS for name in outputs):raise ValueError("Unknown calendar output")
    recover_calendar_transaction(root)
    backup=Path(tempfile.mkdtemp(prefix=".calendar-backup-",dir=root))
    previous={}
    for name in outputs:
        target=root/name
        if target.exists():
            data=target.read_bytes()
            with (backup/name).open("wb") as stream:
                stream.write(data);stream.flush();os.fsync(stream.fileno())
            previous[name]={"existed":True,"sha256":byte_hash(data)}
        else:previous[name]={"existed":False}
    # The journal exists BEFORE the first production-file replacement.
    atomic_json(root/JOURNAL,{"schema":"wrn.calendar-transaction.v1","backupDirectory":backup.name,"previous":previous})
    try:
        for name,data in outputs.items():install_calendar_file(root/name,data)
        verify_calendar_generation(root,allow_pending=True)
    except Exception:
        recover_calendar_transaction(root)
        raise
    # A hard process interruption leaves the journal; news always recovers it.
    (root/JOURNAL).unlink()
    shutil.rmtree(backup)

def verify_calendar_generation(root,*,allow_pending=False):
    if (root/JOURNAL).exists() and not allow_pending:
        raise RuntimeError("Pending calendar transaction; recovery required before publication")
    marker_path=root/"calendar-generation.json"
    if not marker_path.exists():
        # Before first migration there may be a legitimate untouched v1 bundle.
        status=read_json(root/"calendar-status.json",{})
        if status.get("schema")=="wrn.calendar-status.v2":raise ValueError("v2 calendar has no generation marker")
        return {"legacy":True}
    marker=read_json(marker_path,{})
    if marker.get("schema")!="wrn.calendar-generation.v1":raise ValueError("Invalid calendar generation marker")
    expected={"calendar-source-cache.json","events.json","events-feed.json","calendar-status.json"}
    if set(marker.get("files",{}))!=expected:raise ValueError("Incomplete calendar generation manifest")
    for name,digest in marker["files"].items():
        if not (root/name).exists() or byte_hash((root/name).read_bytes())!=digest:
            raise ValueError("Mixed calendar generation: "+name)
    status=read_json(root/"calendar-status.json",{})
    feed_status=read_json(root/"feed-status.json",{})
    if feed_status:
        for key in ["revision","archiveCount","feedCount"]:
            if feed_status.get("events",{}).get(key)!=status.get(key):
                raise ValueError("Calendar status section does not match generation: "+key)
        for key,value in marker.get("eventStatus",{}).items():
            if feed_status.get("events",{}).get(key)!=value:
                raise ValueError("Mixed calendar events status generation: "+key)
    return marker

def guard_before_news_commit(root):
    """Recover partial calendar writes before other news status generation."""
    recover_calendar_transaction(root)
    return verify_calendar_generation(root)

def read_json(path,default):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8-sig"))

def event_status(raw):
    if raw.get("deleted") is True: return "deleted",False
    if raw.get("cancelled") is True or raw.get("canceled") is True: return "cancelled",False
    value=str(raw.get("status") or raw.get("eventStatus") or "").lower().split("/")[-1]
    if not value: return "scheduled",True
    aliases={"scheduled":"scheduled","eventscheduled":"scheduled","confirmed":"scheduled",
             "cancelled":"cancelled","canceled":"cancelled","eventcancelled":"cancelled",
             "deleted":"deleted","eventdeleted":"deleted"}
    if value not in aliases: raise ValueError("unsupported-status:"+value)
    return aliases[value],False

def make_event(source,native_id,title,url,start,end="",raw=None,checked=None):
    raw=raw or {}; checked=checked or stamp()
    start_dt=parse_instant(start); end_dt=parse_instant(end)
    all_day=bool(raw.get("eventAllDay") is True)
    if all_day:
        first=date.fromisoformat(str(start))
        last=date.fromisoformat(str(end)) if end else None
        if last and last<=first: raise ValueError("non-positive-all-day-range")
        start_value=first.isoformat(); end_value=last.isoformat() if last else ""
    else:
        if start_dt is None: raise ValueError("missing-explicit-start-or-offset")
        if end not in ("",None) and end_dt is None: raise ValueError("invalid-end")
        if end_dt and end_dt<start_dt: raise ValueError("end-before-start")
        # A long range may be an exhibition, but cannot be certified as one
        # continuous event from the abbreviated API list alone.
        if end_dt and end_dt-start_dt>timedelta(days=7):
            raise ValueError("long-range-needs-occurrence-review")
        start_value=stamp(start_dt); end_value=stamp(end_dt) if end_dt else ""
    if not text(title) or not safe_url(url) or native_id is None or isinstance(native_id,bool) or not str(native_id).strip(): raise ValueError("missing-identity-title-url")
    status,inferred=event_status(raw)
    ident=source["id"]+":"+str(native_id)
    updated=parse_instant(raw.get("updatedAt") or raw.get("eventUpdated"))
    published=parse_instant(raw.get("createdAt") or raw.get("published"))
    place=raw.get("place") if isinstance(raw.get("place"),dict) else {}
    return {
        "id":ident,"eventOccurrenceId":ident,"eventUuid":ident,"eventApiId":ident,
        "eventSourceId":source["id"],"eventSchemaVersion":2,"eventTimeVerified":True,
        "type":"event","sourceType":"structured-calendar","kontinent":"Radar","categories":["Radar"],
        "quelleName":source["name"],"author":source["name"],"title":text(title),
        "link":url,"sourceHomepage":source["url"],"content":"","contentComplete":False,
        "language":str(raw.get("language") or "und"),"pubDate":stamp(published) if published else "",
        "eventStart":start_value,"eventEnd":end_value,"eventAllDay":all_day,
        "eventDate":start_value[:10] if all_day else "",
        "eventStartDate":start_value if all_day else "","startDate":start_value if all_day else "",
        "eventEndDate":end_value if all_day else "","endDate":end_value if all_day else "",
        "eventTimePrecision":"date" if all_day else "datetime",
        "eventTimezone":str(raw.get("timezone") or ""),"timeZone":str(raw.get("timezone") or ""),
        "eventTimezoneInferred":raw.get("timezoneInferred") is True,
        "eventVenue":text(place.get("name")),"eventAddress":text(place.get("address")),
        "eventCity":text(place.get("city")),"eventCountry":text(place.get("countryCode")),
        "eventLatitude":place.get("latitude") if place.get("latitude") is not None else "",
        "eventLongitude":place.get("longitude") if place.get("longitude") is not None else "",
        "eventTags":[text(t) for t in raw.get("tags",[]) if isinstance(t,str)],
        "eventSeriesId":source["id"]+":"+str(raw["parentId"]) if raw.get("parentId") else "",
        "eventRecurrence":"","eventStatus":status,"eventStatusInferred":inferred,
        "cancelled":status=="cancelled","deleted":status=="deleted",
        "eventUpdated":stamp(updated) if updated else "","updatedAt":stamp(updated) if updated else "",
        "eventCheckedAt":checked,"calendarGenerationAt":checked,"eventRecordUpdatedAt":checked,
        "eventCanonicalOrigin":safe_url(raw.get("ap_id")),"eventAliases":[ident],
        "eventEvidenceUrl":source["url"],"eventDateEvidence":"structured-publisher-start",
    }

def gancio_events(source,rows,checked):
    if not isinstance(rows,list): raise ValueError("Gancio payload is not a list")
    result=[]; rejected=[]
    for raw in rows:
        try:
            if not isinstance(raw,dict): raise ValueError("non-object-row")
            # Real children already have distinct ids/start_datetime; no RRULE expansion.
            if raw.get("rrule") or raw.get("recurrent_rule"): raise ValueError("unexpanded-recurrence")
            slug=urllib.parse.quote(str(raw.get("slug") or raw.get("id") or ""),safe="-")
            url=source["url"].rstrip("/")+"/event/"+slug
            result.append(make_event(source,raw.get("id"),raw.get("title"),url,raw.get("start_datetime"),raw.get("end_datetime"),raw,checked))
        except (ValueError,TypeError) as error:
            rejected.append({"nativeId":raw.get("id") if isinstance(raw,dict) else None,"reason":str(error)})
    return result,rejected

class ListingParser(HTMLParser):
    """Read publisher's event_item blocks, preserving machine-readable start."""
    def __init__(self):
        super().__init__(); self.items=[]; self.item=None; self.depth=0; self.heading=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs); classes=attrs.get("class","").split()
        if tag=="div" and "event_item" in classes:
            self.item={"title":"","status":"scheduled"}; self.depth=1
            for status in ["cancelled","canceled","deleted"]:
                if "status-"+status in classes: self.item["status"]=status
            return
        if self.item is None:return
        if tag=="div": self.depth+=1
        if tag=="a" and "/veranstaltung/" in attrs.get("href",""): self.item["url"]=attrs["href"]
        if tag in ["h3","h4","h5"]: self.heading=True
        if tag=="time" and attrs.get("itemprop") in ["dtstart","startDate"]: self.item["start"]=attrs.get("datetime","")
        if tag=="time" and attrs.get("itemprop") in ["dtend","endDate"]: self.item["end"]=attrs.get("datetime","")
    def handle_data(self,data):
        if self.item is not None and self.heading:self.item["title"]+=data
    def handle_endtag(self,tag):
        if tag in ["h3","h4","h5"]:self.heading=False
        if self.item is not None and tag=="div":
            self.depth-=1
            if self.depth==0:self.items.append(self.item);self.item=None

def ikuwo_events(source,body,checked):
    parser=ListingParser();parser.feed(body)
    if not parser.items: raise ValueError("No machine-readable IKUWO event blocks")
    rows=[];rejected=[]
    for item in parser.items:
        try:
            url=item.get("url","");native=urllib.parse.urlsplit(url).path.strip("/")
            raw={"status":item["status"],"language":"de","place":{"name":"IKUWO","city":"Greifswald","countryCode":"DE"}}
            # Venue comes from this specifically researched organiser, not an instance-name guess.
            rows.append(make_event(source,native,item["title"],url,item.get("start"),item.get("end",""),raw,checked))
        except (ValueError,TypeError) as e:rejected.append({"url":item.get("url"),"reason":str(e)})
    return rows,rejected


class PanelParser(HTMLParser):
    def __init__(self):
        super().__init__();self.items=[];self.item=None;self.depth=0;self.heading=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="div" and "cms-row" in attrs.get("class","").split():
            self.item={"title":"","parts":[]};self.depth=1;return
        if self.item is None:return
        if tag=="div":self.depth+=1
        if tag=="h2":self.heading=True
        if tag=="a" and attrs.get("href","").startswith("/panel/"):self.item["url"]=attrs["href"]
    def handle_data(self,data):
        if self.item is not None:
            self.item["parts"].append(data)
            if self.heading:self.item["title"]+=data
    def handle_endtag(self,tag):
        if tag=="h2":self.heading=False
        if self.item is not None and tag=="div":
            self.depth-=1
            if self.depth==0:self.items.append(self.item);self.item=None

def zinn_events(source,home,panels,checked):
    # The date must be explicit on the current organiser homepage AND the
    # panel-page title must name that same year. Never recycle last year's grid.
    clean=text(home)
    months="January February March April May June July August September October November December".split()
    match=re.search(r"\b("+ "|".join(months)+r")\s+(\d{1,2}),\s+(20\d{2})\b",clean)
    if not match:raise ValueError("Zinn current fair date missing")
    month,day,year=match.groups()
    if not re.search(r"<title>\s*"+year+r"\s+Panels",panels,re.I):raise ValueError("Zinn panel year differs")
    fair_date=date(int(year),months.index(month)+1,int(day))
    if "CCSF Mission Campus" not in clean or "1125 Valencia" not in clean:
        raise ValueError("Zinn venue changed; adapter review needed")
    parser=PanelParser();parser.feed(panels)
    if not parser.items:raise ValueError("Zinn panel rows missing")
    result=[];rejected=[]
    zone=ZoneInfo("America/Los_Angeles")
    for item in parser.items:
        try:
            times=re.findall(r"\b(\d{1,2}):(\d{2})\s*(am|pm)\b"," ".join(item["parts"]),re.I)
            if len(times)<2:raise ValueError("session start/end missing")
            def convert(parts):
                hour,minute,period=parts
                hour=int(hour)%12+(12 if period.lower()=="pm" else 0)
                return datetime.combine(fair_date,datetime.min.time()).replace(hour=hour,minute=int(minute),tzinfo=zone)
            start,end=convert(times[0]),convert(times[1])
            url=urllib.parse.urljoin(source["url"],item.get("url",""))
            raw={"language":"en","timezone":"America/Los_Angeles","timezoneInferred":True,
                "place":{"name":"CCSF Mission Campus","address":"1125 Valencia","city":"San Francisco","countryCode":"US"}}
            row=make_event(source,item.get("url",""),item["title"],url,stamp(start),stamp(end),raw,checked)
            row["eventParentEvent"]="Howard Zinn Book Fair "+str(fair_date.year)
            row["eventDateEvidence"]="current-organiser-fair-date-and-same-year-session-grid"
            result.append(row)
        except (ValueError,TypeError) as e:rejected.append({"url":item.get("url"),"reason":str(e)})
    return result,rejected

def radar_events(source,payload,checked):
    rawrows=payload.get("result") if isinstance(payload,dict) else None
    if not isinstance(rawrows,dict): raise ValueError("Radar result missing")
    rows=[];rejected=[]
    for native,raw in rawrows.items():
        try:
            dates=raw.get("date_time") or []
            if not dates:raise ValueError("missing-event-dates")
            if len(dates)>1 and any(not (b.get("uuid") or b.get("id")) for b in dates):
                raise ValueError("multiple-dates-without-stable-occurrence-id")
            for index,block in enumerate(dates):
                if block.get("rrule"):raise ValueError("rule-only-series-needs-concrete-occurrences")
                locations=raw.get("offline") or []
                location=locations[0] if locations and isinstance(locations[0],dict) else {}
                address=location.get("address") or {}
                adapted={"language":raw.get("language"),"timezone":location.get("timezone") or "",
                    "place":{"name":address.get("name_line") or location.get("title"),"city":address.get("locality"),
                    "address":address.get("thoroughfare"),"countryCode":address.get("country")},
                    "status":raw.get("status") or "scheduled"}
                rows.append(make_event(source,str(native)+(":"+str(block.get("uuid") or block.get("id")) if len(dates)>1 else ""),
                    raw.get("title"),raw.get("url") or "https://radar.squat.net/en/node/"+str(native),
                    block.get("value"),block.get("value2"),adapted,checked))
        except (ValueError,TypeError) as e:rejected.append({"nativeId":native,"reason":str(e)})
    return rows,rejected

def current_event(row,now):
    if row.get("eventSchemaVersion")!=2 or row.get("eventTimeVerified") is not True:return False
    if row.get("eventStatus") in ["deleted","cancelled"]:
        since=parse_instant(row.get("eventTombstoneAt") or row.get("eventRecordUpdatedAt"))
        original_end=parse_instant(row.get("eventEnd") or row.get("eventStart"))
        if row.get("eventAllDay"):
            try: original_end=datetime.combine(date.fromisoformat(row.get("eventEndDate") or row["eventStartDate"]),datetime.min.time(),UTC)
            except (ValueError,KeyError): original_end=None
        horizon=max([d for d in [since,original_end] if d is not None],default=None)
        return horizon is not None and horizon>=now-timedelta(days=TOMBSTONE_DAYS)
    if row.get("eventAllDay") is True:
        try:
            first=date.fromisoformat(row["eventStartDate"])
            end=date.fromisoformat(row["eventEndDate"]) if row.get("eventEndDate") else first+timedelta(days=1)
            zone=row.get("eventTimezone")
            if zone:
                try: today=now.astimezone(ZoneInfo(zone)).date()
                except (ValueError,KeyError): return False
            else:
                # A floating civil date is not a fabricated UTC midnight.
                today=(now-timedelta(hours=12)).date()
            return first<=today+timedelta(days=DAYS) and end>today
        except (ValueError,KeyError):return False
    start=parse_instant(row.get("eventStart"));end=parse_instant(row.get("eventEnd"))
    if not start:return False
    return start<=now+timedelta(days=DAYS) and (end or start+timedelta(hours=2))>=now

def tombstone(row,now,reason):
    row=dict(row);row.update(eventStatus="deleted",deleted=True,cancelled=False,
        eventTombstoneAt=stamp(now),eventRecordUpdatedAt=stamp(now),eventCheckedAt=stamp(now),
        calendarGenerationAt=stamp(now),eventRemovalReason=reason)
    return row

def semantic_signature(row):
    ignored={"eventCheckedAt","calendarGenerationAt","eventRecordUpdatedAt","eventAliases","eventReinstatedFromSnapshot"}
    return hashlib.sha256(json.dumps({k:v for k,v in row.items() if k not in ignored},
        sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def publisher_allows_reinstatement(dead,active):
    active_revision=parse_instant(active.get("eventUpdated"))
    dead_revision=parse_instant(dead.get("eventUpdated") or dead.get("eventTombstoneAt"))
    return bool(active_revision and dead_revision and active_revision>dead_revision)

def preferred_record(a,b):
    """Consumer contract: material revision first, publisher fallback, dead on ties."""
    a_material=parse_instant(a.get("eventRecordUpdatedAt"))
    b_material=parse_instant(b.get("eventRecordUpdatedAt"))
    a_dead=a.get("eventStatus") in ["deleted","cancelled"]
    b_dead=b.get("eventStatus") in ["deleted","cancelled"]
    if a_material and b_material:
        if a_material!=b_material:return a if a_material>b_material else b
        if a_dead!=b_dead:return a if a_dead else b
    else:
        a_publisher=parse_instant(a.get("eventUpdated") or a.get("updatedAt"))
        b_publisher=parse_instant(b.get("eventUpdated") or b.get("updatedAt"))
        if a_publisher and b_publisher and a_publisher!=b_publisher:
            return a if a_publisher>b_publisher else b
        if a_dead!=b_dead:return a if a_dead else b
    return a if (a.get("eventCheckedAt") or "")>=(b.get("eventCheckedAt") or "") else b

def merge_source(previous,new,complete,now):
    old={r["eventOccurrenceId"]:r for r in previous if r.get("eventSchemaVersion")==2 and r.get("eventOccurrenceId")}
    incoming={r["eventOccurrenceId"]:r for r in new}
    output=[]
    for ident,row in incoming.items():
        prior=old.get(ident)
        if prior and prior.get("eventStatus") in ["deleted","cancelled"] and row.get("eventStatus")=="scheduled":
            # A missing-from-snapshot tombstone may be withdrawn by a later
            # actual successful reappearance. Explicit cancellation needs a
            # later publisher modification, not merely a later fetch.
            reappeared=(prior.get("eventRemovalReason")=="missing-from-complete-upcoming-snapshot"
                and parse_instant(row.get("eventCheckedAt")) and parse_instant(prior.get("eventTombstoneAt"))
                and parse_instant(row["eventCheckedAt"])>parse_instant(prior["eventTombstoneAt"]))
            if reappeared:
                row=dict(row);row["eventReinstatedFromSnapshot"]=True
            elif not publisher_allows_reinstatement(prior,row):row=prior
        if prior and semantic_signature(row)==semantic_signature(prior):
            row=dict(row);row["eventRecordUpdatedAt"]=prior.get("eventRecordUpdatedAt") or prior.get("eventCheckedAt")
            if prior.get("eventTombstoneAt"):row["eventTombstoneAt"]=prior["eventTombstoneAt"]
        elif prior:
            # Local material revisions are strictly monotonic for semantic
            # changes, even when publisher timestamps have coarse precision.
            previous_revision=parse_instant(prior.get("eventRecordUpdatedAt"))
            candidate_revision=parse_instant(row.get("eventRecordUpdatedAt"))
            if previous_revision and candidate_revision and candidate_revision<=previous_revision:
                row=dict(row);row["eventRecordUpdatedAt"]=stamp(previous_revision+timedelta(microseconds=1))
        output.append(row)
    for ident,row in old.items():
        if ident in incoming:continue
        if row.get("eventStatus") in ["deleted","cancelled"]:
            if current_event(row,now): output.append(row)
        elif complete and current_event(row,now):
            output.append(tombstone(row,now,"missing-from-complete-upcoming-snapshot"))
        elif not complete: output.append(row)
    return [r for r in output if current_event(r,now)]

def duplicate_key(row):
    if row.get("eventCanonicalOrigin"):return ("origin",row["eventCanonicalOrigin"],row["eventStart"])
    address=norm(row.get("eventAddress"));venue=norm(row.get("eventVenue"))
    # Without explicit place information, don't merge same-title events worldwide.
    if not address or not venue:return ("id",row["eventOccurrenceId"])
    return ("exact-place",norm(row["title"]),row["eventStart"],venue,address)

def deduplicate(rows):
    groups=[]
    for row in rows:
        keys={("id",row["eventOccurrenceId"]),duplicate_key(row)}
        address=norm(row.get("eventAddress"));venue=norm(row.get("eventVenue"))
        if address and venue:
            keys.add(("exact-place",norm(row["title"]),row["eventStart"],venue,address))
        matches=[]
        for group in groups:
            common=group["keys"] & keys
            explicit=any(key[0] in ["id","origin"] for key in common)
            if common and (explicit or row.get("eventSourceId") not in group["sourceIds"]):
                matches.append(group)
        aliases=set(row.get("eventAliases",[]));winner=dict(row)
        source_ids={row.get("eventSourceId")}
        for g in matches:
            keys |= g["keys"];aliases.update(g["row"].get("eventAliases",[]));source_ids |= g["sourceIds"]
            winner=dict(preferred_record(g["row"],winner))
            groups.remove(g)
        winner["eventAliases"]=sorted(aliases)
        groups.append({"keys":keys,"row":winner,"sourceIds":source_ids})
    return sorted([g["row"] for g in groups],key=lambda r:(r.get("eventStart",""),r["eventOccurrenceId"]))


def validate_against_known_tombstones(rows,previous):
    dead_rows=[r for r in [*previous,*rows] if r.get("eventSchemaVersion")==2 and r.get("eventStatus") in ["deleted","cancelled"]]
    result=[]
    def keys(r):
        out={duplicate_key(r)}
        address=norm(r.get("eventAddress"));venue=norm(r.get("eventVenue"))
        if address and venue:out.add(("exact-place",norm(r["title"]),r["eventStart"],venue,address))
        return out
    for row in rows:
        if row.get("eventStatus")!="scheduled":result.append(row);continue
        blocked=None
        for dead in dead_rows:
            same_identity=row["eventOccurrenceId"]==dead["eventOccurrenceId"]
            common=keys(row)&keys(dead)
            explicit_origin=any(key[0]=="origin" for key in common)
            cross_source=row.get("eventSourceId")!=dead.get("eventSourceId")
            if not same_identity and not (common and (explicit_origin or cross_source)):continue
            if same_identity and row.get("eventReinstatedFromSnapshot"):continue
            if publisher_allows_reinstatement(dead,row):
                dead_material=parse_instant(dead.get("eventRecordUpdatedAt"))
                active_material=parse_instant(row.get("eventRecordUpdatedAt"))
                if dead_material and active_material and active_material<=dead_material:
                    # A later publisher revision has just been verified across
                    # this alias group. Emit a later material active revision.
                    row=dict(row)
                    row["eventRecordUpdatedAt"]=stamp(dead_material+timedelta(microseconds=1))
            else:
                blocked=dict(dead)
                blocked["eventAliases"]=sorted(set(dead.get("eventAliases",[])+row.get("eventAliases",[])))
                break
        result.append(blocked or row)
    return result

def fetch(url,evidence,source_id,page):
    request=urllib.request.Request(url,headers={"User-Agent":"WRN-Calendar/2.0 (+https://github.com/Blackfront161/Revolution-News-Data)","Accept":"application/json,text/html"})
    with urllib.request.urlopen(request,timeout=20) as response:
        data=response.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise ValueError("response-size-limit")
        if not safe_url(response.url):raise ValueError("non-HTTPS-redirect")
        receipt={"url":url,"finalUrl":response.url,"status":response.status,"checkedAt":stamp(),
            "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    if evidence:
        name=re.sub("[^a-zA-Z0-9_.-]","_",source_id)+"-"+str(page)
        (evidence/(name+".body")).write_bytes(data);atomic_json(evidence/(name+".receipt.json"),receipt)
    return data.decode("utf-8-sig"),receipt

def collect(source,now,evidence=None,replay=None):
    status={"sourceId":source["id"],"url":source["url"],"complete":False,"checkedAt":stamp(),"state":"failed","rejected":[],"receipts":[]}
    rows=[];observed=set()
    try:
        if replay is not None and source["kind"]=="gancio":
            health=read_json(replay/"gancio-api-health.json",[])
            record=next((r for r in health if r["baseUrl"]==source["url"]),None)
            if not record or not record.get("rawFile"):raise ValueError("no-successful-research-receipt")
            data=(replay/record["rawFile"]).read_bytes()
            if hashlib.sha256(data).hexdigest()!=record["sha256"]:raise ValueError("research-hash-mismatch")
            payload=json.loads(data);checked=record["checkedAt"]
            new,rejected=gancio_events(source,payload,checked)
            complete=len(payload)<PAGE_SIZE and not rejected
            status.update(checkedAt=checked,rawCount=len(payload),complete=complete,
                state="ok" if complete else "partial",rejected=rejected,replay=True)
            return new,status
        if replay is not None:raise ValueError("no-replay-for-this-adapter")
        if source["kind"]=="gancio":
            for page in range(MAX_PAGES):
                query=urllib.parse.urlencode({"start":int((now-timedelta(days=7)).timestamp()),"end":int((now+timedelta(days=DAYS)).timestamp()),"max":PAGE_SIZE,"page":page,"show_recurrent":"true","show_multidate":"true"})
                body,receipt=fetch(source["url"].rstrip("/")+"/api/events?"+query,evidence,source["id"],page)
                status["receipts"].append(receipt)
                payload=json.loads(body)
                if not isinstance(payload,list):raise ValueError("non-list-api")
                signature=hashlib.sha256(body.encode()).hexdigest()
                if signature in observed:raise ValueError("pagination-repeats-page")
                observed.add(signature)
                new,rejected=gancio_events(source,payload,receipt["checkedAt"])
                rows.extend(new);status["rejected"].extend(rejected)
                status["checkedAt"]=receipt["checkedAt"]
                status["rawCount"]=status.get("rawCount",0)+len(payload)
                if len(payload)<PAGE_SIZE:status["complete"]=True;break
            if status["rejected"]:status["complete"]=False
            status["state"]="ok" if status["complete"] else "partial"
        elif source["kind"]=="ikuwo":
            body,receipt=fetch(source["url"],evidence,source["id"],0)
            status["receipts"].append(receipt)
            rows,status["rejected"]=ikuwo_events(source,body,receipt["checkedAt"])
            # The list may be paginated/limited by organiser; no absence-based deletion.
            status.update(state="partial",complete=False,checkedAt=receipt["checkedAt"])
        elif source["kind"]=="zinn":
            home,receipt=fetch(source["url"],evidence,source["id"],0)
            panels,panel_receipt=fetch(source["url"].rstrip("/")+"/panels",evidence,source["id"],1)
            status["receipts"].extend([receipt,panel_receipt])
            rows,status["rejected"]=zinn_events(source,home,panels,panel_receipt["checkedAt"])
            status.update(state="partial",complete=False,checkedAt=panel_receipt["checkedAt"])
        elif source["kind"]=="radar":
            # Radar's range/rule semantics do not certify a complete occurrence snapshot.
            body,receipt=fetch(source["url"]+"?limit=500",evidence,source["id"],0)
            status["receipts"].append(receipt)
            rows,status["rejected"]=radar_events(source,json.loads(body),receipt["checkedAt"])
            status.update(state="partial",complete=False,checkedAt=receipt["checkedAt"])
        else:raise ValueError("adapter-not-enabled")
    except Exception as e:
        status.update(state="partial" if rows else "failed",error=type(e).__name__+": "+str(e))
    return rows,status

def refresh(root,now=None,evidence=None,replay=None):
    now=now or datetime.now(UTC)
    recover_calendar_transaction(root)
    registry=read_json(root/"calendar-sources.json",{})["sources"]
    previous=read_json(root/"events.json",[])
    # Keep independent source histories so exact federated deduplication never
    # resets a suppressed alias's material revision at the next successful poll.
    cache=read_json(root/"calendar-source-cache.json",{})
    grouped=cache.get("sources",{}) if cache.get("schema")=="wrn.calendar-source-cache.v2" else {}
    if not grouped:
        for row in previous:
            if isinstance(row,dict) and row.get("eventSchemaVersion")==2:
                grouped.setdefault(row.get("eventSourceId",""),[]).append(row)
    snapshots={};statuses=[]
    active=[s for s in registry if s.get("enabled") is True]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        work={pool.submit(collect,s,now,evidence,replay):s for s in active}
        for future in concurrent.futures.as_completed(work):
            source=work[future];new,status=future.result();statuses.append(status)
            snapshots[source["id"]]=merge_source(grouped.get(source["id"],[]),new,status["complete"],now)
    successful=sum(s["state"]!="failed" for s in statuses)
    if not successful:raise RuntimeError("All calendar sources failed; no published files changed")
    validated=validate_against_known_tombstones(
        [r for source_rows in snapshots.values() for r in source_rows],previous)
    validated_active={r["eventOccurrenceId"]:r for r in validated if r.get("eventStatus")=="scheduled"}
    for source_rows in snapshots.values():
        for row in source_rows:
            if row["eventOccurrenceId"] in validated_active:
                row["eventRecordUpdatedAt"]=validated_active[row["eventOccurrenceId"]]["eventRecordUpdatedAt"]
    rows=deduplicate(validated)
    # Publish every eligible row; feed cap is explicitly separate, tombstones reserved.
    active_rows=[r for r in rows if r.get("eventStatus")=="scheduled"]
    tombstones=[r for r in rows if r.get("eventStatus")!="scheduled"]
    feed=deduplicate(active_rows[:2000]+tombstones)
    revision=hashlib.sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    status={"schema":"wrn.calendar-status.v2","snapshotScope":"configured-sources-120-day-window",
        "authoritativeCompleteSnapshot":False,"minimumEventSchemaVersion":2,"legacyUpcomingPolicy":"quarantine-v1","generatedAt":stamp(now),"revision":revision,
        "state":"ok" if all(s["state"]=="ok" for s in statuses) else "partial",
        "sources":sorted(statuses,key=lambda s:s["sourceId"]),"archiveCount":len(rows),"feedCount":len(feed),
        "scheduledCount":len(active_rows),"tombstoneCount":len(tombstones),
        "legacyQuarantined":sum(r.get("eventSchemaVersion")!=2 for r in previous if isinstance(r,dict)),
        "note":"Successful fetch verifies source data, not independent real-world organiser confirmation."}
    # A complete batch can legitimately cancel/remove every active event.
    # merge_source retained last-good rows for partial/failed sources already;
    # all-source failure was rejected above. Never suppress valid tombstones
    # merely because no active row remains.
    outputs={}
    outputs["calendar-source-cache.json"]=json_bytes({
        "schema":"wrn.calendar-source-cache.v2","generatedAt":stamp(now),"sources":snapshots})
    outputs["events.json"]=json_bytes(rows)
    outputs["events-feed.json"]=json_bytes(feed)
    outputs["calendar-status.json"]=json_bytes(status)
    feed_status=read_json(root/"feed-status.json",{})
    if feed_status:
        feed_status["events"]={"revision":revision,"archiveCount":len(rows),"feedCount":len(feed),
            "bytes":len(outputs["events-feed.json"]),"lastSuccessfulFetchAt":stamp(now),
            "sourceState":status["state"],"authoritativeCompleteSnapshot":False}
        outputs["feed-status.json"]=json_bytes(feed_status)
    outputs["calendar-generation.json"]=json_bytes({
        "schema":"wrn.calendar-generation.v1","revision":revision,
        "eventStatus":{key:feed_status["events"][key] for key in
            ["revision","archiveCount","feedCount","bytes","lastSuccessfulFetchAt","sourceState"]} if feed_status else {},
        "files":{name:byte_hash(data) for name,data in outputs.items() if name!="feed-status.json"}})
    commit_calendar_generation(root,outputs)
    return status

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--evidence-dir",type=Path);parser.add_argument("--replay-research",type=Path)
    parser.add_argument("--recover-only",action="store_true")
    parser.add_argument("--verify-generation",action="store_true")
    args=parser.parse_args()
    if args.recover_only:
        recover_calendar_transaction(args.root);return
    if args.verify_generation:
        if (args.root/JOURNAL).exists():raise RuntimeError("Pending calendar transaction; recover before committing")
        verify_calendar_generation(args.root);return
    if args.evidence_dir:args.evidence_dir.mkdir(parents=True,exist_ok=True)
    status=refresh(args.root,evidence=args.evidence_dir,replay=args.replay_research)
    print(json.dumps({k:v for k,v in status.items() if k!="sources"},ensure_ascii=False))
if __name__=="__main__":main()
