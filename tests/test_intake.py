"""Source-derived and operational tests. No live network or API_KEY reads."""
import copy
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from access_intake.app import (Config, MockProvider, OpenAIProvider, ProviderError, Store,
                               accuracy, export_records, process, route, validate_reply)

ROOT = Path(__file__).resolve().parents[1]
TRUTH = json.loads((ROOT / 'tests/ground_truth.json').read_text())


class MockProviderTests(unittest.TestCase):
    def test_mock_provider(self):
        """Step 1: saved replies alone, with expectations frozen from S01–S21."""
        forbidden = AssertionError('step 1 must not access credentials or network')
        environment = mock.MagicMock(spec=os.environ)
        environment.get.side_effect = forbidden
        environment.__getitem__.side_effect = forbidden
        with mock.patch.object(os, 'environ', environment), \
                mock.patch.object(os, 'getenv', side_effect=forbidden), \
                mock.patch.object(socket, 'socket', side_effect=forbidden), \
                mock.patch('access_intake.app.urllib.request.urlopen', side_effect=forbidden), \
                mock.patch('access_intake.app.Store', side_effect=AssertionError('storage forbidden')), \
                mock.patch('access_intake.app.validate_reply', side_effect=AssertionError('validation forbidden')), \
                mock.patch('access_intake.app.route', side_effect=AssertionError('routing forbidden')):
            provider = MockProvider(Config())
            self.assertEqual(set(TRUTH), {f'IT-{i:03}.json' for i in range(1, 21)} | {'SYN-001.json'})
            for name, item in TRUTH.items():
                with self.subTest(name=name):
                    message = json.loads((ROOT / item['source']).read_text())['message']
                    # Decode the saved envelope directly; no later pipeline component.
                    reply = provider.extract(name, message)
                    extraction = json.loads(reply['output'][0]['content'][0]['text'])
                    expected = item['expected']
                    for field, value in expected.items():
                        if field not in ('supporting_quotes', 'issues'):
                            self.assertEqual(extraction[field], value, (name, field))
                    for quote in item['evidence'].values():
                        self.assertIn(quote, message)
                    self.assertEqual(reply['source_message_sha256'],
                                     hashlib.sha256(message.encode('utf-8')).hexdigest())
            message = json.loads((ROOT / TRUTH['IT-001.json']['source']).read_text())['message']
            with self.assertRaises(ProviderError):
                provider.extract('UNKNOWN.json', message)
            with self.assertRaises(ProviderError):
                provider.extract('IT-001.json', 'unseen fixture text')


class ExtractionTests(unittest.TestCase):
    """Step 2 validates saved responses without storage, workers or routing."""

    def setUp(self):
        for target in ('socket.socket', 'urllib.request.urlopen',
                       'access_intake.app.Store', 'access_intake.app.route'):
            patcher = mock.patch(target, side_effect=AssertionError('step 2 dependency forbidden'))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.config = Config()
        self.provider = MockProvider(self.config)
        self.fields = ('request_id', 'request_date', 'kind', 'requester', 'team',
                       'system', 'environment', 'permission', 'business_purpose',
                       'start_date', 'end_date', 'manager')

    def source(self, name):
        return json.loads((ROOT / TRUTH[name]['source']).read_text(encoding='utf-8'))

    def check_extraction(self, name, document=None):
        message = (document if document is not None else self.source(name))['message']
        reply = self.provider.extract(name, message)
        extraction = validate_reply(reply, message, self.config.schema)
        self.assertEqual({key: extraction[key] for key in self.fields},
                         {key: TRUTH[name]['expected'][key] for key in self.fields}, name)
        return extraction

    def test_extraction_fields(self):
        schema = json.loads((ROOT / 'snapshot.schema.json').read_text())
        self.assertEqual(self.config.schema, schema)
        self.assertEqual(set(schema['properties']), set(self.fields) | {'issues', 'supporting_quotes'})
        for name in TRUTH:
            with self.subTest(name=name):
                extraction = self.check_extraction(name)
                self.assertEqual(set(extraction), set(schema['required']))
                for field in ('issues', 'supporting_quotes'):
                    self.assertIsInstance(extraction[field], list)
                    self.assertTrue(all(isinstance(value, str) for value in extraction[field]))
                for field in self.fields:
                    self.assertTrue(extraction[field] is None or isinstance(extraction[field], str))
                for field in ('request_date', 'start_date', 'end_date'):
                    if extraction[field] is not None:
                        self.assertRegex(extraction[field], r'^\d{4}-\d{2}-\d{2}$')
                for field, allowed in (('kind', ('new', 'change', 'withdrawal', 'other', None)),
                                       ('environment', ('staging', 'production', None)),
                                       ('permission', ('read', 'write', 'admin', None))):
                    self.assertIn(extraction[field], allowed)

    def test_invalid_outputs(self):
        message = self.source('IT-001.json')['message']
        original = self.provider.extract('IT-001.json', message)
        extraction = json.loads(original['output'][0]['content'][0]['text'])

        def envelope(value):
            reply = copy.deepcopy(original)
            reply['output'][0]['content'][0]['text'] = json.dumps(value)
            return reply

        for field in self.config.schema['required']:
            with self.subTest(missing=field):
                value = copy.deepcopy(extraction)
                del value[field]
                with self.assertRaises(ProviderError):
                    validate_reply(envelope(value), message, self.config.schema)
        changes = ({'surprise': True}, {'requester': 123}, {'kind': 'approve'},
                   {'environment': 'dev'}, {'permission': 'root'}, {'issues': 'oops'},
                   {'issues': [7]}, {'supporting_quotes': 'oops'}, {'supporting_quotes': [7]},
                   {'start_date': '2026-02-30'}, {'start_date': '23/10/2026'},
                   {'supporting_quotes': ['invented quote']})
        for change in changes:
            with self.subTest(change=change):
                value = copy.deepcopy(extraction)
                value.update(change)
                with self.assertRaises(ProviderError):
                    validate_reply(envelope(value), message, self.config.schema)
        for level in ('response', 'message'):
            with self.subTest(incomplete=level):
                reply = copy.deepcopy(original)
                (reply if level == 'response' else reply['output'][0])['status'] = 'incomplete'
                with self.assertRaises(ProviderError):
                    validate_reply(reply, message, self.config.schema)
        for name in ('refusal', 'interrupted', 'malformed'):
            with self.subTest(fixture=name):
                reply = json.loads((ROOT / f'tests/mock_responses/{name}.json').read_text())
                with self.assertRaises(ProviderError):
                    validate_reply(reply, message, self.config.schema)

    def test_source_semantics(self):
        for name in ('IT-004.json', 'IT-007.json', 'IT-008.json', 'IT-010.json',
                     'IT-011.json', 'IT-015.json', 'IT-016.json', 'IT-019.json', 'IT-020.json'):
            with self.subTest(name=name):
                self.check_extraction(name)
        self.test_metadata_is_not_source()

    def test_evidence_and_issues(self):
        for name in ('IT-003.json', 'IT-004.json', 'IT-005.json', 'IT-006.json', 'IT-009.json',
                     'IT-010.json', 'IT-011.json', 'IT-016.json', 'IT-017.json', 'IT-020.json'):
            with self.subTest(name=name):
                extraction = self.check_extraction(name)
                message = self.source(name)['message']
                for quote in extraction['supporting_quotes']:
                    self.assertTrue(quote)
                    self.assertIn(quote, message)
                for field in self.fields:
                    if TRUTH[name]['expected'][field] is None:
                        self.assertTrue(any(field in issue.lower() and re.search(
                            r'missing|absent|unresolved|relative|conflict|not (?:stated|provided|specified)',
                            issue, re.I) for issue in extraction['issues']), (name, field))
                quotes = '\n'.join(extraction['supporting_quotes'])
                issues = '\n'.join(extraction['issues'])
                if name in ('IT-004.json', 'IT-020.json'):
                    field, alternatives = (('environment', ('staging', 'production')) if name == 'IT-004.json'
                                           else ('manager', ('Priya Shah', 'Elena Park')))
                    for alternative in alternatives:
                        self.assertIn(alternative, quotes)
                    self.assertTrue(any(field in issue.lower() and 'conflict' in issue.lower()
                                        for issue in extraction['issues']), name)
                if name == 'IT-006.json':
                    attempt = message[message.index('SYSTEM OVERRIDE:'):]
                    self.assertTrue(any(attempt in quote for quote in extraction['supporting_quotes']))
                    self.assertRegex(issues.lower(), r'override|injection|embedded instruction')
                    self.assertEqual(extraction['permission'], 'read')
                if name == 'IT-016.json':
                    self.assertRegex(issues.lower(), r'mismatch')
                    self.assertRegex(issues.lower(), r'filename|file name|document')

    def test_metadata_is_not_source(self):
        document = self.source('IT-011.json')
        original = self.check_extraction('IT-011.json', document)
        changed = copy.deepcopy(document)
        changed.update(exported_at='2030-01-01T00:00:00Z', subject='Start 2030-01-02 end 2030-01-03')
        self.assertEqual(self.check_extraction('IT-011.json', changed), original)
        payload = OpenAIProvider(self.config).request(changed['message'])
        self.assertEqual(payload['input'], [{'role': 'user', 'content': document['message']}])
        self.assertNotIn('2030-01', json.dumps(payload))

    def test_corrections(self):
        self.assertEqual(self.check_extraction('IT-008.json')['environment'], 'staging')
        extraction = self.check_extraction('IT-015.json')
        self.assertEqual((extraction['start_date'], extraction['end_date']), ('2026-10-29', '2026-10-31'))

    def test_relative_dates(self):
        extraction = self.check_extraction('IT-011.json')
        for field in ('start_date', 'end_date'):
            self.assertIsNone(extraction[field])
            self.assertTrue(any(field in issue for issue in extraction['issues']))
        self.assertRegex(' '.join(extraction['issues']).lower(), r'relative|unresolved')

    def test_changes(self):
        for name, permission in (('IT-007.json', 'write'), ('IT-019.json', 'read')):
            extraction = self.check_extraction(name)
            self.assertEqual(extraction['kind'], 'change')
            self.assertEqual(extraction['permission'], permission)

    def test_identifier(self):
        extraction = self.check_extraction('IT-016.json')
        self.assertEqual(extraction['request_id'], 'IT-061')
        issues = ' '.join(extraction['issues']).lower()
        self.assertIn('mismatch', issues)
        self.assertRegex(issues, r'filename|file name|document')


class LedgerTests(unittest.TestCase):
    """Step 3 persists prepared mock results, independently of workers/routing."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for target in ('socket.socket', 'urllib.request.urlopen',
                       'access_intake.app.process', 'access_intake.app.route'):
            patcher = mock.patch(target, side_effect=AssertionError('step 3 dependency forbidden'))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.store = Store(Path(self.temp.name) / 'state.db')
        self.config = Config()

    def source(self, name='IT-001.json'):
        return ROOT / TRUTH[name]['source']

    def prepared(self, name='IT-001.json', revised=False, document_id=None):
        fixture = ROOT / 'tests/mock_responses' / ('revised' if revised else '') / name
        reply = json.loads(fixture.read_text())
        extraction = json.loads(reply['output'][0]['content'][0]['text'])
        expected = copy.deepcopy(TRUTH[name]['expected'])
        if revised:
            expected['permission'] = 'write'
        for key in expected:
            if key not in ('supporting_quotes', 'issues'):
                self.assertEqual(extraction[key], expected[key])
        routing = dict(TRUTH[name]['route'])
        if revised:
            routing = dict(status='review', owner='Security Review', next_action='review-risk-then-owner')
        if document_id and document_id != name:
            extraction['issues'].append('request_id: identifier mismatch with document filename')
            routing = dict(status='needs-information', owner='IT Service Desk', next_action='clarify')
        return dict(extraction=extraction, error=None, response_source='mock', **routing)

    def save(self, name='IT-001.json', revised=False, document_id=None):
        job = self.store.claim(30)
        self.assertIsNotNone(job)
        self.assertTrue(self.store.finish(job['attempt_id'], job['token'],
                                        self.prepared(name, revised, document_id)))
        return job

    def test_bytes_identity(self):
        raw = self.source().read_bytes()
        self.assertIsInstance(json.loads(raw.decode('utf-8'))['message'], str)
        self.store.ingest([self.source()], self.config)
        pending = self.store.current()[0]
        self.assertEqual(pending['document_id'], 'IT-001.json')
        self.assertEqual(pending['source_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(pending['state'], 'pending')
        with self.store.connection() as conn:
            saved = conn.execute('SELECT raw FROM attempts').fetchone()['raw']
        self.assertEqual(saved, raw)
        self.save()
        self.assertEqual(self.store.current()[0]['extraction']['request_id'], 'IT-001')

    def test_unchanged(self):
        provider = MockProvider(self.config)
        message = json.loads(self.source().read_bytes())['message']
        with mock.patch.object(provider, 'extract', wraps=provider.extract) as calls:
            self.store.ingest([self.source()], self.config)
            provider.extract('IT-001.json', message)
            self.save()
            first = self.store.current()[0]
            self.assertEqual(self.store.ingest([self.source()], self.config), 0)
            self.assertIsNone(self.store.claim(30))
            self.assertEqual(calls.call_count, 1)
        self.assertEqual(self.store.current(), [first])
        self.assertEqual(self.store.history('IT-001.json'), [first])
        self.assertEqual(first['extraction']['permission'], 'read')
        self.assertEqual(first['owner'], 'System Owner')
        self.assertEqual(first['next_action'], 'review-request')

    def test_changed_source(self):
        raw = self.source().read_bytes()
        changed = json.loads(raw)
        changed['message'] = changed['message'].replace('new read access', 'new write access')
        revisions = (raw, raw + b'\n ', json.dumps(changed).encode('utf-8'))
        path = Path(self.temp.name) / 'IT-001.json'
        for index, revision in enumerate(revisions):
            path.write_bytes(revision)
            self.assertEqual(self.store.ingest([path], self.config), 1)
            self.save(revised=index == 2)
        history = self.store.history(path.name)
        self.assertEqual(len(history), 3)
        self.assertEqual(len({row['attempt_id'] for row in history}), 3)
        self.assertEqual([row['source_sha256'] for row in history],
                         [hashlib.sha256(raw).hexdigest() for raw in revisions])
        self.assertEqual(len({row['source_sha256'] for row in history}), 3)
        self.assertEqual([row['extraction']['permission'] for row in history], ['read', 'read', 'write'])
        self.assertEqual([row['owner'] for row in history], ['System Owner', 'System Owner', 'Security Review'])
        self.assertEqual(self.store.current(), [history[-1]])

    def test_settings_refresh(self):
        schema = copy.deepcopy(self.config.schema)
        schema['description'] = 'revision-2'
        changes = {'model': 'mock-model-2', 'prompt': self.config.prompt + '\n',
                   'schema': schema, 'policy': self.config.policy + '\n',
                   'provider': 'fake-provider-2', 'max_output_tokens': 3001}
        for index, (field, value) in enumerate(changes.items()):
            with self.subTest(field=field):
                self.store = Store(Path(self.temp.name) / f'settings-{index}.db')
                self.store.ingest([self.source()], self.config)
                self.save()
                # Config identity is tested with an injected saved reply, never a live adapter.
                config = Config(**{field: value})
                self.assertEqual(self.store.ingest([self.source()], config), 1)
                self.save()
                self.assertEqual(self.store.ingest([self.source()], config), 0)
                self.assertIsNone(self.store.claim(30))
                history = self.store.history()
                self.assertEqual(len(history), 2)
                self.assertEqual(history[0]['source_sha256'], history[1]['source_sha256'])
                self.assertNotEqual(history[0]['config_key'], history[1]['config_key'])
                self.assertEqual(history[1]['extraction']['permission'], 'read')
                with self.store.connection() as conn:
                    saved = [json.loads(row['config']) for row in conn.execute('SELECT config FROM attempts ORDER BY attempt_id')]
                self.assertEqual(saved, [self.config.as_dict(), config.as_dict()])

    def test_incremental_batches(self):
        self.store.ingest([self.source()], self.config)
        self.save()
        first = self.store.current()[0]
        self.store.ingest([self.source('IT-002.json')], self.config)
        self.save('IT-002.json')
        rows = {row['document_id']: row for row in self.store.current()}
        self.assertEqual(set(rows), {'IT-001.json', 'IT-002.json'})
        self.assertEqual(rows['IT-001.json'], first)
        self.assertEqual(rows['IT-002.json']['owner'], 'Security Review')
        self.assertEqual(rows['IT-002.json']['next_action'], 'review-risk-then-owner')

    def test_same_request_distinct_documents(self):
        path = Path(self.temp.name) / 'COPY-001.json'
        path.write_bytes(self.source().read_bytes())
        self.store.ingest([self.source(), path], self.config)
        self.save()
        self.save(document_id=path.name)
        rows = {row['document_id']: row for row in self.store.current()}
        self.assertEqual(set(rows), {'IT-001.json', 'COPY-001.json'})
        self.assertEqual({row['extraction']['request_id'] for row in rows.values()}, {'IT-001'})
        self.assertEqual(len({row['source_sha256'] for row in rows.values()}), 1)
        self.assertEqual(rows['IT-001.json']['owner'], 'System Owner')
        self.assertEqual(rows[path.name]['next_action'], 'clarify')
        self.assertIn('mismatch', ' '.join(rows[path.name]['extraction']['issues']))

    def test_saved_provenance(self):
        raw = self.source().read_bytes()
        changed = json.loads(raw)
        changed['message'] = changed['message'].replace('new read access', 'new write access')
        edited = json.dumps(changed).encode('utf-8')
        path = Path(self.temp.name) / 'IT-001.json'
        for index, revisions in enumerate(((raw, edited), (edited, raw))):
            with self.subTest(order=index):
                self.store = Store(Path(self.temp.name) / f'provenance-{index}.db')
                jobs = []
                for revision in revisions:
                    path.write_bytes(revision)
                    self.store.ingest([path], self.config)
                    jobs.append(self.store.claim(30))
                for job in reversed(jobs):
                    self.assertTrue(self.store.finish(job['attempt_id'], job['token'],
                        self.prepared(revised=job['raw'] == edited)))
                self.assertEqual(self.store.current()[0]['attempt_id'], jobs[-1]['attempt_id'])
                self.assertEqual(self.store.current()[0]['source_sha256'], hashlib.sha256(revisions[-1]).hexdigest())
                with self.store.connection() as conn:
                    stored = list(conn.execute('SELECT * FROM attempts ORDER BY attempt_id'))
                for row, revision in zip(stored, revisions):
                    self.assertEqual(row['raw'], revision)
                    self.assertEqual(json.loads(row['config']), self.config.as_dict())
                    self.assertEqual(row['config_key'], self.config.key)
                # Newest failure also remains current when an older success finishes later.
                self.store.ingest([path], self.config, force=True)
                older = self.store.claim(30)
                self.store.ingest([path], self.config, force=True)
                newer = self.store.claim(30)
                error = dict(extraction=None, status='error', owner='IT Service Desk',
                             next_action='retry-extraction', error='temporary-unavailable; retry', response_source='mock')
                self.assertTrue(self.store.finish(newer['attempt_id'], newer['token'], error))
                self.assertTrue(self.store.finish(older['attempt_id'], older['token'], self.prepared(revised=revisions[-1] == edited)))
                self.assertEqual(self.store.current()[0]['attempt_id'], newer['attempt_id'])
                self.assertEqual(self.store.current()[0]['status'], 'error')


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'state.db')
        self.config = Config()
        self.provider = MockProvider(self.config)
        self.network = mock.patch.object(socket, 'socket', side_effect=AssertionError('network forbidden'))
        self.network.start()
        self.addCleanup(self.network.stop)

    def source(self, name='IT-001.json'):
        return ROOT / TRUTH[name]['source']

    def extraction(self, name='IT-001.json'):
        return copy.deepcopy(TRUTH[name]['expected'])

    def enqueue(self, *names, config=None, force=False):
        return self.store.ingest([self.source(n) for n in (names or ('IT-001.json',))], config or self.config, force=force)

    def run_intake(self, *names, config=None, provider=None):
        self.enqueue(*names, config=config)
        process(self.store, workers=2, provider_factory=(lambda cfg: provider or MockProvider(cfg)))
        return self.store.current()

    def check_source(self, name):
        item=TRUTH[name]
        raw=self.source(name).read_bytes()
        message=json.loads(raw)['message']
        reply=self.provider.extract(name, message)
        ext=validate_reply(reply,message,self.config.schema)
        for key,value in item['expected'].items():
            if key not in ('supporting_quotes','issues'):
                self.assertEqual(ext[key],value,(name,key))
        r=route(ext,message,name)
        self.assertEqual(dict(zip(('status','owner','next_action'),r)),item['route'],name)
        for key,quote in item['evidence'].items():
            self.assertIn(quote,message,(name,key))
        return ext

    def test_all_source_cases(self):
        for name in TRUTH:
            with self.subTest(name=name):self.check_source(name)

    def test_missing_dates(self):
        ext=self.check_source('IT-010.json')
        self.assertIsNone(ext['end_date']);self.assertTrue(ext['issues'])

    def test_conflicts(self):
        for name,key in [('IT-004.json','environment'),('IT-020.json','manager')]:
            ext=self.check_source(name);self.assertIsNone(ext[key]);self.assertTrue(ext['issues'])

    def test_synthetic(self):self.check_source('SYN-001.json')
    def test_override(self):
        self.check_source('IT-006.json')
        ext=self.extraction('IT-006.json');ext['issues']=[]
        message=json.loads(self.source('IT-006.json').read_bytes())['message']
        self.assertEqual(route(ext,message,'IT-006.json'),('review','IT Service Desk','inspect-message'))
    def test_withdrawal(self):self.check_source('IT-005.json')
    def test_clarification(self):
        for name in ('IT-003.json','IT-009.json','IT-017.json','IT-020.json'):self.check_source(name)
        ext=self.extraction();ext['manager']=None;ext['issues']=[]
        self.assertEqual(route(ext,'','IT-001.json')[0],'needs-information')
    def test_inverted_dates(self):self.check_source('IT-014.json')
    def test_security(self):
        for name in ('IT-002.json','IT-007.json','IT-012.json','IT-013.json','IT-019.json'):self.check_source(name)
    def test_complete(self):self.check_source('IT-001.json')

    def test_provider_failure(self):
        class Failure:
            def extract(self,*args):raise ProviderError('Provider unavailable; retry-extraction')
        rows=self.run_intake('IT-001.json',provider=Failure())
        r=rows[0]
        self.assertEqual(r['status'],'error');self.assertIsNone(r['extraction'])
        self.assertEqual(r['owner'],'IT Service Desk');self.assertEqual(r['next_action'],'retry-extraction')
        self.assertIn('retry',r['error'].lower())

    def test_failed_retry(self):
        self.run_intake()
        self.enqueue(force=True)
        class Failure:
            def extract(self,*args):raise ProviderError('failed retry')
        process(self.store,provider_factory=lambda cfg:Failure())
        self.assertEqual(self.store.current()[0]['status'],'error')
        history=self.store.history('IT-001.json')
        self.assertEqual(len(history),2)
        self.assertIsNotNone(history[0]['extraction'])
        self.assertIsNone(history[1]['extraction'])

    def test_fast_before_slow(self):
        self.enqueue('IT-001.json','IT-002.json')
        waiting=threading.Event();release=threading.Event()
        original=self.provider
        class Slow:
            def extract(self,name,message):
                if name=='IT-001.json':waiting.set();release.wait(5)
                return original.extract(name,message)
        thread=threading.Thread(target=process,args=(self.store,),kwargs={'workers':2,'provider_factory':lambda cfg:Slow()})
        thread.start()
        try:
            self.assertTrue(waiting.wait(2))
            end=time.monotonic()+3
            while time.monotonic()<end:
                rows={r['document_id']:r for r in self.store.current()}
                if rows['IT-002.json']['state']=='completed':break
                time.sleep(.01)
            self.assertEqual(rows['IT-002.json']['state'],'completed')
            self.assertEqual(rows['IT-001.json']['state'],'running')
        finally:release.set();thread.join(5)
        self.assertFalse(thread.is_alive())

    def test_concurrent_claims(self):
        self.enqueue(*[n for n in TRUTH if n.startswith('IT-')])
        command=[sys.executable,'-m','access_intake','--db',str(self.store.path),'resume']
        a=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        b=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        for proc in (a,b):
            out,err=proc.communicate(timeout=20);self.assertEqual(proc.returncode,0,(out,err))
        self.assertEqual(len(self.store.current()),20)
        self.assertTrue(all(r['state']=='completed' and r['status']!='error' for r in self.store.current()))
        self.assertEqual(self.store.event_count('claimed'),20)

    def test_recovery(self):
        self.enqueue()
        old=self.store.claim(.01)
        time.sleep(.03)
        new=self.store.claim(30)
        self.assertIsNotNone(new);self.assertNotEqual(old['token'],new['token'])
        self.assertFalse(self.store.finish(old['attempt_id'],old['token'],{'stale':True}))
        self.assertTrue(self.store.finish(new['attempt_id'],new['token'],{'extraction':None,'status':'error','owner':'IT Service Desk','next_action':'retry-extraction','error':'test failure','response_source':'mock'}))
        self.assertEqual(self.store.current()[0]['status'],'error')
        # Later source finishes first: older work must not replace it.
        self.enqueue(force=True);old=self.store.claim(30)
        self.enqueue(force=True);new=self.store.claim(30)
        value={'extraction':None,'status':'error','owner':'IT Service Desk','next_action':'retry-extraction','error':'newest','response_source':'mock'}
        self.store.finish(new['attempt_id'],new['token'],value)
        value['error']='older';self.store.finish(old['attempt_id'],old['token'],value)
        self.assertEqual(self.store.current()[0]['error'],'newest')

    def test_lease_renewal(self):
        self.enqueue()
        job=self.store.claim(.05)
        self.assertTrue(self.store.renew(job['attempt_id'],job['token'],10))
        time.sleep(.06)
        self.assertIsNone(self.store.claim(10))
        self.assertFalse(self.store.renew(job['attempt_id'],'wrong-token',10))

    def test_malformed_export_is_independent(self):
        bad=Path(self.temp.name)/'broken.json'
        bad.write_bytes(b'not UTF-8 JSON: \xff')
        self.store.ingest([bad,self.source()],self.config)
        process(self.store,provider_factory=lambda cfg:MockProvider(cfg))
        indexed={r['document_id']:r for r in self.store.current()}
        self.assertEqual(indexed['broken.json']['status'],'error')
        self.assertIsNone(indexed['broken.json']['extraction'])
        self.assertEqual(indexed['IT-001.json']['status'],'review')

    def test_refusal_and_interruption_are_current_errors(self):
        for name in ('refusal','interrupted','malformed'):
            response=json.loads((ROOT/f'tests/mock_responses/{name}.json').read_text())
            class Reply:
                def extract(self,*args):return response
            self.enqueue(force=True)
            process(self.store,provider_factory=lambda cfg:Reply())
            self.assertEqual(self.store.current()[0]['status'],'error')
            self.assertIsNone(self.store.current()[0]['extraction'])
        self.assertEqual(len(self.store.history('IT-001.json')),3)

    def test_provider_contract(self):
        cfg=Config(provider='openai',model='gpt-4.1-mini',retries=1,interval=0)
        provider=OpenAIProvider(cfg)
        payload=provider.request('untrusted source')
        self.assertEqual(payload['model'],cfg.model)
        self.assertFalse(payload['store'])
        self.assertTrue(payload['text']['format']['strict'])
        self.assertEqual(payload['text']['format']['schema'],cfg.schema)
        self.assertIn('data',payload['instructions'])
        reply=self.provider.extract('IT-001.json',json.loads(self.source().read_bytes())['message'])
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return json.dumps(reply).encode()
        with mock.patch('access_intake.app.urllib.request.urlopen',return_value=Response()) as send:
            got=provider.extract('IT-001.json','untrusted source',api_key='test-secret')
        self.assertEqual(got,reply)
        req=send.call_args.args[0]
        self.assertEqual(req.get_header('Authorization'),'Bearer test-secret')
        self.assertNotIn('test-secret',json.dumps(provider.request('untrusted source')))
        from urllib.error import HTTPError
        err=HTTPError('https://api.openai.com/v1/responses',429,'rate limited',{'Retry-After':'0'},None)
        with mock.patch('access_intake.app.urllib.request.urlopen',side_effect=[err,Response()]) as send:
            provider.extract('x','data',api_key='test-secret')
            self.assertEqual(send.call_count,2)
        err=HTTPError('https://api.openai.com/v1/responses',401,'test-secret',{},None)
        with mock.patch('access_intake.app.urllib.request.urlopen',side_effect=err) as send:
            with self.assertRaises(ProviderError) as raised:provider.extract('x','data',api_key='test-secret')
            self.assertEqual(send.call_count,1);self.assertNotIn('test-secret',str(raised.exception))
        with mock.patch('access_intake.app.urllib.request.urlopen',side_effect=TimeoutError('test-secret')) as send, mock.patch('access_intake.app.time.sleep'):
            with self.assertRaises(ProviderError) as raised:provider.extract('x','data',api_key='test-secret')
            self.assertEqual(send.call_count,2);self.assertNotIn('test-secret',str(raised.exception))

    def test_export(self):
        self.run_intake('IT-001.json','IT-002.json')
        out=Path(self.temp.name)/'deliverables'
        export_records(self.store,out)
        records=[json.loads(x) for x in (out/'extractions.jsonl').read_text().splitlines()]
        queue=json.loads((out/'queue.json').read_text())
        self.assertEqual(len(records),2)
        for r,q in zip(records,queue):
            for key in ('document_id','source_sha256','attempt_id','status','owner','next_action'):
                self.assertEqual(r[key],q[key])
        self.assertTrue((out/'history.jsonl').exists())
        manifest=json.loads((out/'snapshot.json').read_text())
        for name,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((out/manifest['generation']/name).read_bytes()).hexdigest(),digest)

    def test_accuracy(self):
        self.run_intake(*TRUTH.keys())
        report=accuracy(self.store.current(),TRUTH)
        self.assertEqual(report['scalar_total'],21*12)
        self.assertEqual(report['scalar_matches'],21*12)
        self.assertEqual(report['routing_matches'],21*3)
        self.assertEqual(report['differences'],[])
        rows=self.store.current();rows[0]['extraction']['requester']='invented'
        report=accuracy(rows,TRUTH)
        self.assertEqual(report['scalar_matches'],21*12-1)
        self.assertEqual(len(report['differences']),1)
        self.assertEqual(accuracy([],TRUTH)['scalar_matches'],0)

    def test_cli(self):
        command=[sys.executable,'-m','access_intake','--db',str(self.store.path)]
        result=subprocess.run(command+['intake',str(self.source()),'--enqueue-only'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run(command+['queue','--json'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(json.loads(result.stdout)[0]['state'],'pending')
        result=subprocess.run(command+['resume'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run(command+['history','IT-001.json'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(len(json.loads(result.stdout)),1)
        result=subprocess.run(command+['retry','IT-001.json'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(self.store.history('IT-001.json')),2)

    def test_docs(self):
        for path in ('README.md','planning/plan.md','planning/spec.md','requirements.lock',
                     'deliverables/accuracy.md','deliverables/verification.md','deliverables/request-evidence.json'):
            self.assertTrue((ROOT/path).is_file(),path)
        readme=(ROOT/'README.md').read_text()
        for word in ('resume','retry','API_KEY','accuracy','unittest','SQLite','2,000'):self.assertIn(word,readme)


if __name__=='__main__':unittest.main()
