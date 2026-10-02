import unittest
from unittest.mock import Mock
import check_radio_streams as radio
import check_audio_sources as audio


class RadioChecks(unittest.TestCase):
    def test_directory_is_not_marked_playable(self):
        _, health = radio.probe_station({'id': 'x', 'name': 'X', 'website': 'https://example.org'})
        self.assertFalse(health['ok'])
        self.assertEqual(health['audioStatus'], 'unknown')
        self.assertTrue(health['checkedAt'])

    def test_fallback_and_stop_after_success(self):
        probe = Mock(side_effect=[{'status': 'broken', 'url': 'https://x/a'}, {'status': 'playable', 'url': 'https://x/b'}])
        _, health = radio.probe_station({'id': 'x', 'name': 'X', 'streamCandidates': ['https://x/a', 'https://x/b', 'https://x/c']}, probe)
        self.assertEqual(probe.call_count, 2)
        self.assertEqual(health['workingStream'], 'https://x/b')
        self.assertTrue(health['ok'])

    def test_empty_or_html_audio_response_rejected_and_closed(self):
        for body in (b'', b'<!DOCTYPE html><html>Error</html>'):
            response = Mock(status_code=200, headers={'Content-Type': 'audio/mpeg'}, url='https://x/live')
            response.iter_content.return_value = [body]
            session = Mock()
            session.get.return_value = response
            result = audio.test_url(session, 'https://x/live')
            self.assertEqual(result['status'], 'limited')
            response.close.assert_called_once()

    def test_nonempty_audio_and_http_error_close_connection(self):
        for code, expected in [(200, 'playable'), (404, 'broken'), (429, 'limited')]:
            response = Mock(status_code=code, headers={'Content-Type': 'audio/mpeg'}, url='https://x/live')
            response.iter_content.return_value = [b'ID3test']
            session = Mock()
            session.get.return_value = response
            self.assertEqual(audio.test_url(session, 'https://x/live')['status'], expected)
            response.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
