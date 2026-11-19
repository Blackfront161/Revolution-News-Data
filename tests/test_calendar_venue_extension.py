"""Exact venue regression fixtures; no network or copied event content."""
from copy import deepcopy
from unittest import TestCase
import update_calendar as calendar


PLACES = (
    ("offbeat.amsterdam",21,"Paradiso","Weteringschans 6, 1017 SG Amsterdam","Amsterdam","NL"),
    ("offbeat.amsterdam",20,"Melkweg","Lijnbaansgracht 234A, 1017 PH Amsterdam","Amsterdam","NL"),
    ("offbeat.amsterdam",16,"NieuwLand","Pieter Nieuwlandstraat 93, 1093 XN Amsterdam","Amsterdam","NL"),
    ("offbeat.amsterdam",53,"Tolhuistuin","IJpromenade 2, 1031 KT Amsterdam","Amsterdam","NL"),
    ("offbeat.amsterdam",10,"Vrankrijk","Spuistraat 216, 1012 VT Amsterdam","Amsterdam","NL"),
    ("flyinghigh-bonn.org",9,"Kult 41","Hochstadenring 41, 53119 Bonn","Bonn","DE"),
)
CHECKED = "2026-11-19T19:00:00Z"


class VenueLocationExtensionTest(TestCase):
    def test_geography_and_conflict_guards_for_each_verified_venue(self):
        for host, place_id, name, address, city, country in PLACES:
            with self.subTest(name=name):
                source = {"id":"gancio:"+host,"url":"https://"+host,"name":host}
                raw = {"id":100,"title":"Fixture","start_datetime":"2026-12-05T20:00:00+01:00",
                       "place":{"id":place_id,"name":name,"address":address}}
                before = deepcopy(raw)
                for status in ("scheduled", "cancelled", "deleted"):
                    event = {**raw, "status":status}
                    rows, rejected = calendar.gancio_events(source, [event], CHECKED)
                    self.assertFalse(rejected)
                    old_shape = calendar.make_event(
                        source,raw["id"],raw["title"],rows[0]["link"],raw["start_datetime"],
                        raw=event,checked=CHECKED,
                    )
                    self.assertEqual(rows,[{**old_shape,"eventCity":city,"eventCountry":country}])
                self.assertEqual(raw,before)
                for k, v in (("id",str(place_id)),("id",float(place_id)),("id",True),
                             ("name",name+" "),("address",address+" "),("city","Other"),
                             ("countryCode","XX")):
                    other = {**raw,"place":{**raw["place"],k:v}}
                    self.assertIs(calendar.reviewed_venue_location(source,other),other)
                lookalike = {**source,"url":"https://elsewhere.example"}
                self.assertIs(calendar.reviewed_venue_location(lookalike,raw),raw)
