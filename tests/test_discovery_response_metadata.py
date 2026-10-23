from unittest.mock import Mock, patch
import check_news_sources as checker


def test_legacy_discovery_without_metadata_removes_old_values_without_inventing_200():
    result = {'httpStatus':404, 'contentType':'text/html', 'finalUrl':'https://example.org/old'}
    checker.apply_discovered_response_metadata(result, {'url':'https://example.org/rss'})
    assert result == {'finalUrl':'https://example.org/rss'}


def test_both_recovery_paths_use_actual_replacement_response_metadata():
    for old_status in (404, 200):
        response = Mock(status_code=old_status, url='https://example.org/old',
                        headers={'Content-Type':'text/html'})
        session = Mock()
        session.get.return_value = response
        candidate = {'url':'https://example.org/rss', 'feedType':'xml',
                     'httpStatus':206, 'contentType':'application/rss+xml'}
        with patch.object(checker,'make_session',return_value=session), \
             patch.object(checker,'read_limited',return_value=b'<html>not a feed</html>'), \
             patch.object(checker,'discover_replacement_feed',return_value=candidate):
            result=checker.check_source({'name':'Example','url':'https://example.org/old'})
        assert result['ok'] is True
        assert result['httpStatus']==206  # copied, never a synthetic 200
        assert result['contentType']=='application/rss+xml'
        assert result['finalUrl']==candidate['url']
        assert result['configuredUrl']=='https://example.org/old'


def test_html_200_without_valid_replacement_does_not_become_success():
    response=Mock(status_code=200,url='https://example.org/feed',headers={'Content-Type':'text/html'})
    session=Mock();session.get.return_value=response
    with patch.object(checker,'make_session',return_value=session), \
         patch.object(checker,'read_limited',return_value=b'<html>Hosting suspended</html>'), \
         patch.object(checker,'discover_replacement_feed',return_value=None):
        result=checker.check_source({'name':'Offline','url':'https://example.org/feed'})
    assert result['ok'] is False
    assert result['status']!='ok'
    assert result['httpStatus']==200


def test_targeted_check_preserves_other_publisher_alias_sharing_replacement_feed(monkeypatch):
    shared='https://example.org/feed'
    checked={'name':'Topic','url':shared,'status':'ok','ok':True,'httpStatus':200}
    untouched={'name':'Main','url':shared,'status':'warning','ok':False,'httpStatus':429}
    monkeypatch.setenv('WRN_NEWS_SOURCE_NAMES','Topic')
    monkeypatch.setattr(checker,'load_sources',lambda:[{'name':'Main','url':shared},
                                                    {'name':'Topic','url':'https://example.org/topic/feed'}])
    monkeypatch.setattr(checker,'check_source',lambda _:dict(checked))
    monkeypatch.setattr(checker,'read_json',lambda *args:{'sources':[untouched,checked]})
    monkeypatch.setattr(checker,'read_recovery_json',lambda *args:{})
    monkeypatch.setattr(checker,'apply_history',lambda rows,history:(rows,{},{}))
    monkeypatch.setattr(checker,'write_recovery_json',lambda *args:None)
    captured=[]
    monkeypatch.setattr(checker,'write_results',lambda rows:captured.extend(rows))
    assert checker.main()==0
    by_name={row['name']:row for row in captured}
    assert by_name['Main']==untouched
    assert by_name['Topic']['url']==shared
    assert set(by_name)=={'Main','Topic'}
