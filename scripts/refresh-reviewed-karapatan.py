"""Refresh the existing reviewed Philippines source without copying body/media."""
import datetime, hashlib, json, sys, urllib.request, xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from email.utils import parsedate_to_datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from source_import_policy import metadata_article, restrict_existing_article
POLICY = {
    'name':'Karapatan (Human Rights)', 'kind':'news', 'adapter':'rss',
    'homepage':'https://www.karapatan.org/', 'feedUrl':'https://www.karapatan.org/feed/',
    'languages':['en'], 'categories':['Asia','Movement News'],
    'originCountry':'Philippines', 'originCountryCode':'PH', 'originRegion':'Southeast Asia',
    'operator':'KARAPATAN Alliance (publisher self-description)',
    'sourceType':'Philippine human-rights alliance; solidarity source, not labelled anarchist or Indigenous-owned',
    'reviewEvidence':['https://www.karapatan.org/about/'], 'status':'approved', 'action':'enrich_only',
    'importMode':'metadata-only', 'reviewedAt':'2026-10-03',
    'rightsReview':'Metadata and original links only; no body, PDF or media reuse grant.',
    'metadataTopicOverrides':{'https://www.karapatan.org/5561/':{
        'title':'Primer on Desaparecidos','topics':['Anti-Rep & Prisons']}}
}
def validate_publisher_url(url):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname!='www.karapatan.org' or parsed.username or parsed.password:
        raise ValueError('Karapatan metadata redirect must stay on the reviewed HTTPS publisher host')
class SamePublisherRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_publisher_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    opener=urllib.request.build_opener(SamePublisherRedirect())
    with opener.open(POLICY['feedUrl'],timeout=25) as response:
        validate_publisher_url(response.url)
        data=response.read(3*1024*1024+1)
        if len(data)>3*1024*1024: raise ValueError('Feed exceeds metadata bound')
        final=response.url
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): raise ValueError('Unsafe XML')
    root=ET.fromstring(data); admitted=[]
    for item in root.findall('.//item')[:15]:
        entry={'title':item.findtext('title'),'link':item.findtext('link'),
               'published':item.findtext('pubDate'), 'author':item.findtext('{http://purl.org/dc/elements/1.1/}creator') or 'Unknown'}
        try: when=parsedate_to_datetime(entry['published'])
        except (ValueError,TypeError): continue
        if when.tzinfo is None or not now-datetime.timedelta(days=30)<=when<=now: continue
        row=metadata_article(POLICY,entry,'Asia')
        if row: admitted.append(row)
    if not admitted: raise ValueError('No dated current same-host metadata entries')
    registry=json.loads((ROOT/'multilingual-source-registry.json').read_text(encoding='utf-8'))
    registry['sources']=[r for r in registry['sources'] if r.get('name')!=POLICY['name']]+[POLICY]
    news=json.loads((ROOT/'news.json').read_text(encoding='utf-8'))
    rows={r['link']:r for r in news}
    for key, value in list(rows.items()):
        if value.get('quelleName')==POLICY['name']:
            restricted=restrict_existing_article(value,[POLICY])
            if restricted: rows[key]=restricted
            else: del rows[key]
    for row in admitted: rows[row['link']]=row
    for name,obj in [('multilingual-source-registry.json',registry),('news.json',list(rows.values()))]:
        (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    evidence=ROOT/'docs/evidence/podcast-queue-repair-2026-10-03'; evidence.mkdir(parents=True,exist_ok=True)
    report={'observedAtUTC':now.isoformat(),'feedUrl':POLICY['feedUrl'],'finalUrl':final,
            'inputSha256':hashlib.sha256(data).hexdigest(),'sourcePolicy':POLICY,
            'admittedMetadata':admitted,'scope':'No bodies, PDFs, images or audio saved; title/date/author/original only.'}
    (evidence/'karapatan-intake.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(admitted)} current Karapatan metadata/original links admitted')
if __name__=='__main__': main()
