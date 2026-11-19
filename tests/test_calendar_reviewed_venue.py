"""Reviewed venue metadata is strictly additive; no network or publisher run."""
import copy
import unittest

import update_calendar as calendar


class ReviewedVenueLocationTest(unittest.TestCase):
    source = {
        "id": "gancio:events.rheinmain.social",
        "url": "https://events.rheinmain.social",
        "name": "RheinMain",
    }
    raw = {
        "id": 9001,
        "title": "Fixture concert",
        "slug": "fixture-concert",
        "start_datetime": "2026-12-05T20:00:00+01:00",
        "place": {
            "id": 72,
            "name": "Haus Mainusch",
            "address": "Staudingerweg 23, 55128 Mainz",
        },
    }
    checked = "2026-11-19T18:00:00Z"

    def test_exact_tuple_adds_only_two_fields_to_same_occurrence(self):
        original = copy.deepcopy(self.raw)
        rows, rejected = calendar.gancio_events(self.source, [self.raw], self.checked)
        self.assertFalse(rejected)
        self.assertEqual(len(rows), 1)
        event = rows[0]
        self.assertEqual((event["eventCity"], event["eventCountry"]), ("Mainz", "DE"))
        expected = calendar.make_event(
            self.source, self.raw["id"], self.raw["title"], event["link"],
            self.raw["start_datetime"], raw=self.raw, checked=self.checked,
        )
        self.assertEqual(event, {**expected, "eventCity": "Mainz", "eventCountry": "DE"})
        self.assertEqual(self.raw, original)

    def test_location_is_not_inferred_for_changed_place_or_source(self):
        for field, value in (("id", 73), ("id", "72"), ("name", "Other"), ("address", "Other")):
            raw = copy.deepcopy(self.raw)
            raw["place"][field] = value
            self.assertIs(calendar.reviewed_venue_location(self.source, raw), raw)
        for field, value in (("id", "gancio:other"), ("url", "https://elsewhere.org")):
            source = {**self.source, field: value}
            self.assertIs(calendar.reviewed_venue_location(source, self.raw), self.raw)

    def test_explicit_data_and_conflicts_are_untouched(self):
        for city, country in (("Berlin", ""), ("", "FR"), ("Mainz", "DE"), ("mainz", "DE")):
            raw = copy.deepcopy(self.raw)
            raw["place"].update(city=city, countryCode=country)
            self.assertIs(calendar.reviewed_venue_location(self.source, raw), raw)

    def test_existing_matching_field_gets_only_missing_companion(self):
        for key, value in (("city", "Mainz"), ("countryCode", "DE")):
            raw = copy.deepcopy(self.raw)
            raw["place"][key] = value
            result = calendar.reviewed_venue_location(self.source, raw)
            self.assertEqual(result["place"], {**self.raw["place"], "city": "Mainz", "countryCode": "DE"})
            self.assertEqual(raw["place"], {**self.raw["place"], key: value})

    def test_explicit_tombstones_are_not_revived_by_metadata(self):
        for status in ("cancelled", "deleted"):
            rows, rejected = calendar.gancio_events(self.source, [{**self.raw, status: True}], self.checked)
            self.assertFalse(rejected)
            self.assertEqual(rows[0]["eventStatus"], status)
            self.assertTrue(rows[0][status])
