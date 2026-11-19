"""A nominally complete Rebaltela list is not deletion evidence."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

import update_calendar as calendar

SOURCE = {
    "id": "gancio:rebaltela.org",
    "kind": "gancio",
    "url": "https://rebaltela.org",
    "name": "rebaltela.org",
    "enabled": True,
}
NOW = calendar.parse_instant("2026-11-19T17:27:57.938558Z")


def fixture(native_id):
    return calendar.make_event(
        SOURCE, native_id, "Fixture event "+str(native_id),
        SOURCE["url"]+"/event/fixture-"+str(native_id), "2026-11-28T21:00:00Z",
        checked="2026-11-19T08:24:02Z",
    )


class RebaltelaAbsencePolicyTest(TestCase):
    def test_source_identity_and_complete_boundary(self):
        self.assertFalse(calendar.absence_allows_removal(SOURCE, {"complete":True}))
        for key, value in (("id","other"),("kind","other"),("url","https://example.org")):
            self.assertTrue(calendar.absence_allows_removal({**SOURCE,key:value},{"complete":True}))
        self.assertFalse(calendar.absence_allows_removal({"id":"else"},{"complete":False}))

    def test_refresh_omission_preserves_active_bytes_explicit_cancel_and_prior_deletion(self):
        prior=fixture(1621)
        prior_gone=calendar.tombstone(fixture(1638),NOW,"missing-from-complete-upcoming-snapshot")
        active=fixture(1625)
        cancelled=deepcopy(active)
        cancelled.update(eventStatus="cancelled",cancelled=True,eventStatusInferred=False)
        receipt={"sourceId":SOURCE["id"],"state":"ok","complete":True,"rawCount":24}
        with TemporaryDirectory() as d:
            root=Path(d)
            calendar.atomic_json(root/"calendar-sources.json",{"sources":[SOURCE]})
            calendar.atomic_json(root/"events-v2.json",[prior,prior_gone,active])
            with mock.patch.object(calendar,"collect",return_value=([cancelled],receipt)):
                calendar.refresh(root,NOW)
            rows={r["eventOccurrenceId"]:r for r in calendar.read_json(root/"events-v2.json",[])}
            self.assertEqual(rows[prior["id"]],prior)
            self.assertEqual(rows[prior_gone["id"]],prior_gone)
            self.assertEqual(rows[active["id"]]["eventStatus"],"cancelled")
            status=calendar.read_json(root/"calendar-status.json",{})["sources"][0]
            self.assertTrue(status["complete"])
            self.assertFalse(status["absenceAllowsRemoval"])
            legacy=calendar.read_json(root/"events.json",[])
            self.assertEqual([r["id"] for r in legacy],[prior["id"]])
