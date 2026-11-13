"""Source-derived and operational tests. No live network or API_KEY reads."""
import copy
import hashlib
import json
import os
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

    def test_bytes_identity(self):
        self.enqueue()
        current=self.store.current()[0]
        self.assertEqual(current['document_id'],'IT-001.json')
        self.assertEqual(current['source_sha256'],hashlib.sha256(self.source().read_bytes()).hexdigest())
        self.assertEqual(current['state'],'pending')

    def test_unchanged(self):
        self.run_intake()
        self.enqueue()
        self.assertEqual(len(self.store.history('IT-001.json')),1)
        self.assertEqual(len(self.store.current()),1)
        self.assertIsNone(self.store.claim(30))

    def test_changed_source(self):
        self.run_intake()
        old=self.store.current()[0]
        p=Path(self.temp.name)/'IT-001.json'
        p.write_bytes(self.source().read_bytes()+b'\n ')
        self.store.ingest([p],self.config)
        self.assertEqual(len(self.store.history(p.name)),2)
        self.assertNotEqual(old['source_sha256'],self.store.current()[0]['source_sha256'])
        process(self.store,provider_factory=lambda cfg: MockProvider(cfg))
        self.assertEqual(len(self.store.current()),1)
        self.assertEqual(self.store.history(p.name)[0]['source_sha256'],old['source_sha256'])
        revised=json.loads(self.source().read_text())
        revised['message']=revised['message'].replace('new read access','new write access')
        p.write_text(json.dumps(revised))
        # The response is independently authored from the explicit changed source span.
        reply=json.loads((ROOT/'tests/mock_responses/revised/IT-001.json').read_text())
        class Revised:
            def extract(self,*args):return reply
        self.store.ingest([p],self.config)
        process(self.store,provider_factory=lambda cfg:Revised())
        latest=self.store.current()[0]
        self.assertEqual(latest['extraction']['permission'],'write')
        self.assertEqual(latest['owner'],'Security Review')
        history=self.store.history(p.name)
        self.assertEqual(len(history),3)
        self.assertEqual(history[0]['extraction']['permission'],'read')
        self.assertNotEqual(history[0]['source_sha256'],latest['source_sha256'])

    def test_settings_refresh(self):
        self.run_intake()
        for key in ('model','prompt','policy'):
            cfg=Config(**{key:getattr(self.config,key)+'\nchanged'})
            self.enqueue(config=cfg)
        self.assertEqual(len(self.store.history('IT-001.json')),4)
        schema=copy.deepcopy(self.config.schema)
        schema['description']='A schema revision'
        self.enqueue(config=Config(schema=schema))
        self.assertEqual(len(self.store.history('IT-001.json')),5)

    def test_incremental_batches(self):
        self.run_intake('IT-001.json')
        self.run_intake('IT-002.json')
        self.assertEqual(len(self.store.current()),2)

    def test_all_source_cases(self):
        for name in TRUTH:
            with self.subTest(name=name):self.check_source(name)

    def test_invalid_outputs(self):
        message=json.loads(self.source().read_bytes())['message']
        for name in ('refusal','interrupted','malformed'):
            with self.subTest(name=name),self.assertRaises(ProviderError):
                validate_reply(json.loads((ROOT/f'tests/mock_responses/{name}.json').read_text()),message,self.config.schema)
        for change in ({'surprise':True},{'permission':'root'},{'start_date':'2026-02-30'},
                       {'supporting_quotes':['invented quote']},{'requester':123}, {'issues':'oops'}):
            ext=self.extraction();ext.update(change)
            with self.subTest(change=change),self.assertRaises(ProviderError):
                validate_reply({'status':'completed','output':[{'type':'message','status':'completed','content':[{'type':'output_text','text':json.dumps(ext)}]}]},message,self.config.schema)
        ext=self.extraction();del ext['manager']
        with self.assertRaises(ProviderError):
            validate_reply({'status':'completed','output':[{'type':'message','status':'completed','content':[{'type':'output_text','text':json.dumps(ext)}]}]},message,self.config.schema)

    def test_metadata_is_not_source(self):
        ext=self.check_source('IT-011.json')
        self.assertIsNone(ext['start_date'])
        self.assertIsNone(ext['end_date'])
        payload=OpenAIProvider(self.config).request('source text only')
        self.assertEqual(payload['input'][0]['content'],'source text only')
        self.assertNotIn('exported_at',payload['input'][0]['content'])

    def test_missing_dates(self):
        ext=self.check_source('IT-010.json')
        self.assertIsNone(ext['end_date']);self.assertTrue(ext['issues'])

    def test_conflicts(self):
        for name,key in [('IT-004.json','environment'),('IT-020.json','manager')]:
            ext=self.check_source(name);self.assertIsNone(ext[key]);self.assertTrue(ext['issues'])

    def test_corrections(self):
        self.assertEqual(self.check_source('IT-008.json')['environment'],'staging')
        self.assertEqual(self.check_source('IT-015.json')['start_date'],'2026-10-29')

    def test_relative_dates(self):self.assertIsNone(self.check_source('IT-011.json')['start_date'])
    def test_changes(self):
        for name in ('IT-007.json','IT-019.json'):self.assertEqual(self.check_source(name)['kind'],'change')
    def test_identifier(self):self.assertEqual(self.check_source('IT-016.json')['request_id'],'IT-061')
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
