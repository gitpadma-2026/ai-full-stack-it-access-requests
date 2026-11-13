"""Durable, independent access-request extraction and human-review preparation."""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCALARS = ('request_id','request_date','kind','requester','team','system','environment',
           'permission','business_purpose','start_date','end_date','manager')
REQUIRED = tuple(k for k in SCALARS if k != 'kind')
OVERRIDE = re.compile(r'system\s+override|bypass\s+approval|highest.priority\s+system|'
                      r'(?:ignore|override)\s+(?:all\s+)?(?:previous|prior|system)\s+instructions|'
                      r'(?:display|reveal|print)\s+(?:the\s+)?api\s*key|mark\s+request\s+as\s+approved',re.I)


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ProviderError(Exception):
    """Safe, operator-facing failure; never contains raw provider response bodies."""


class Config:
    def __init__(self, provider='mock', model='gpt-4.1-mini', prompt=None, policy=None,
                 schema=None, mock_dir=None, timeout=30., retries=2, interval=.1,
                 max_output_tokens=3000, mock_digest=None):
        # Saved configuration identifies injected adapters as well as built-in providers.
        # Worker dispatch below requires an explicit adapter for other identities.
        if not isinstance(provider,str) or not provider.strip():
            raise ValueError('provider must be a nonempty identifier')
        if timeout <= 0 or retries not in range(6) or interval < 0 or max_output_tokens < 1:
            raise ValueError('timeout/tokens must be positive, retries 0..5, interval nonnegative')
        self.provider, self.model = provider, model
        self.prompt = prompt if prompt is not None else (ROOT/'access_intake/prompt.txt').read_text()
        self.policy = policy if policy is not None else (ROOT/'materials/office-policy.md').read_text()
        self.schema = schema if schema is not None else json.loads((ROOT/'snapshot.schema.json').read_text())
        self.mock_dir = str(Path(mock_dir or ROOT/'tests/mock_responses').resolve())
        self.timeout, self.retries, self.interval = float(timeout), retries, float(interval)
        self.max_output_tokens = max_output_tokens
        self.mock_digest = mock_digest if mock_digest is not None else self.fixture_digest()

    def fixture_digest(self):
        return sha(''.join(p.name+sha(p.read_bytes()) for p in sorted(Path(self.mock_dir).glob('*.json'))).encode())

    def as_dict(self):
        return dict(vars(self))

    @property
    def key(self):
        values=self.as_dict()
        if self.provider != 'mock':
            values.pop('mock_digest');values.pop('mock_dir')
        values['engine_version']='2'
        return sha(dump(values).encode())

    @property
    def lease_seconds(self):
        # Every request/retry is bounded, including max Retry-After and process-local rate wait.
        return max(120., (self.retries+1)*(self.timeout+30+self.interval)+60)


class MockProvider:
    def __init__(self, config):
        self.config=config
        if config.fixture_digest()!=config.mock_digest:
            raise ProviderError('Mock fixtures changed since enqueue; re-intake to refresh processing settings')

    def extract(self, document_id, message):
        path=Path(self.config.mock_dir)/(Path(document_id).stem+'.json')
        if not path.is_file():
            raise ProviderError('No saved mock reply for this document; add a labelled fixture or use --provider openai and retry')
        reply=json.loads(path.read_text())
        if reply.get('source_message_sha256')!=sha(message.encode()):
            raise ProviderError('Saved mock reply does not match message content; add a fixture or use the live provider and retry')
        return reply


class OpenAIProvider:
    endpoint='https://api.openai.com/v1/responses'

    def __init__(self,config):
        self.config=config

    def request(self,message):
        return {'model':self.config.model,'store':False,
                'instructions':self.config.prompt+'\nOffice policy (trusted context):\n'+self.config.policy,
                'input':[{'role':'user','content':message}],
                'max_output_tokens':self.config.max_output_tokens,
                'text':{'format':{'type':'json_schema','name':'access_request',
                                  'strict':True,'schema':self.config.schema}}}

    def extract(self,document_id,message,api_key=None):
        key=api_key if api_key is not None else os.environ.get('API_KEY')
        if not key:
            raise ProviderError('API_KEY is unset; set it for live mode then retry, or use mock mode')
        body=dump(self.request(message)).encode()
        for attempt in range(self.config.retries+1):
            request=urllib.request.Request(self.endpoint,data=body,
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
            delay=min(2**attempt,30)
            try:
                with urllib.request.urlopen(request,timeout=self.config.timeout) as response:
                    raw=response.read(2_000_001)
                if len(raw)>2_000_000:
                    raise ProviderError('Provider reply exceeds 2 MB; inspect configuration and retry')
                return json.loads(raw)
            except urllib.error.HTTPError as exc:
                retryable=exc.code==429 or exc.code>=500
                if not retryable or attempt==self.config.retries:
                    raise ProviderError(f'Provider HTTP {exc.code}; check credentials/quota/configuration and retry') from None
                try:delay=min(max(float(exc.headers.get('Retry-After',delay)),0),30)
                except (ValueError,AttributeError):pass
            except (urllib.error.URLError,TimeoutError,OSError):
                if attempt==self.config.retries:
                    raise ProviderError('Provider connection/timeout failure; check connectivity then retry') from None
            except (ValueError,UnicodeError):
                raise ProviderError('Provider returned malformed JSON; inspect configuration then retry') from None
            time.sleep(delay)
        raise ProviderError('Provider retries exhausted; retry extraction')


def validate_reply(reply,message,schema):
    if not isinstance(reply,dict) or reply.get('status')!='completed' or reply.get('error'):
        raise ProviderError('Provider response not completed; retry extraction')
    texts=[]
    output=reply.get('output')
    if not isinstance(output,list):raise ProviderError('Provider output is malformed; retry extraction')
    for item in output:
        if not isinstance(item,dict):raise ProviderError('Invalid output item; retry extraction')
        if item.get('type')=='message':
            if item.get('status')!='completed':raise ProviderError('Interrupted message; retry extraction')
            content=item.get('content')
            if not isinstance(content,list):raise ProviderError('Malformed message content; retry extraction')
            for part in content:
                if not isinstance(part,dict):raise ProviderError('Malformed content part; retry extraction')
                if part.get('type')=='refusal':raise ProviderError('Provider refused the request; inspect message before retry')
                if part.get('type')=='output_text':texts.append(part.get('text'))
    if len(texts)!=1 or not isinstance(texts[0],str):
        raise ProviderError('Expected exactly one structured extraction; retry extraction')
    try:ext=json.loads(texts[0])
    except (ValueError,TypeError):raise ProviderError('Malformed extraction JSON; retry extraction') from None
    if not isinstance(ext,dict) or set(ext)!=set(schema['required']):
        raise ProviderError('Extraction has missing/additional schema fields; retry extraction')
    for field,rule in schema['properties'].items():
        value=ext[field]
        if rule['type']=='array':
            if not isinstance(value,list) or not all(isinstance(x,str) for x in value):
                raise ProviderError(f'Invalid string array {field}; retry extraction')
        elif value is not None and not isinstance(value,str):
            raise ProviderError(f'Invalid scalar {field}; retry extraction')
        if 'enum' in rule and value not in rule['enum']:
            raise ProviderError(f'Invalid enum {field}; retry extraction')
    if not ext['supporting_quotes'] or any(not q or q not in message for q in ext['supporting_quotes']):
        raise ProviderError('Supporting quotes are empty or not exact source substrings; retry extraction')
    for field in ('request_date','start_date','end_date'):
        value=ext[field]
        if value is not None:
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError()
                dt.date.fromisoformat(value)
            except ValueError:raise ProviderError(f'Invalid calendar date {field}; retry extraction') from None
    # Missing values must be visible even if a model omitted the explanatory issue.
    for field in SCALARS:
        if ext[field] is None and not any(field in issue for issue in ext['issues']):
            ext['issues'].append(field+': missing or unresolved in source message')
    return ext


def route(ext,message,document_id):
    """Ordered policy. This function prepares human work; it never grants access."""
    issues=ext['issues']
    rid=ext['request_id']
    # Preserve identity evidence even when an earlier policy rule determines routing.
    filename_id=Path(document_id).stem
    if rid and filename_id!=rid:
        if not any('mismatch' in x for x in issues):
            issues.append('request_id: identifier mismatch with document filename')
    override=OVERRIDE.search(message)
    if override or any(re.search(r'instruction.?override|injection|embedded instruction',x,re.I) for x in issues):
        # Keep the full attempted instruction, not just the detector's trigger phrase.
        if override and message not in ext['supporting_quotes']:
            ext['supporting_quotes'].append(message)
        if not any('instruction-override' in x for x in issues):issues.append('instruction-override attempt in source; inspect original message')
        return 'review','IT Service Desk','inspect-message'
    if ext['kind']=='withdrawal' and ext['request_id'] and ext['request_date']:
        return 'review','IT Service Desk','confirm-withdrawal'
    if ext['start_date'] and ext['end_date'] and ext['start_date']>ext['end_date']:
        if not any('start_date after' in x for x in issues):issues.append('start_date after end_date')
    # Issues concerning corrected source values can be informational. Unresolved conflicts remain blockers.
    conflict=any(re.search(r'conflict|mismatch|start_date after|unresolved',x,re.I) for x in issues)
    if ext['kind'] not in ('new','change') or any(not ext[k] for k in REQUIRED) or conflict:
        return 'needs-information','IT Service Desk','clarify'
    if ext['environment']=='production' or ext['permission'] in ('write','admin'):
        return 'review','Security Review','review-risk-then-owner'
    return 'review','System Owner','review-request'


class Store:
    def __init__(self,path):
        self.path=Path(path).resolve()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS documents(document_id TEXT PRIMARY KEY, current_attempt INTEGER);
            CREATE TABLE IF NOT EXISTS attempts(
              attempt_id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT NOT NULL,
              source_sha256 TEXT NOT NULL, config_key TEXT NOT NULL, raw BLOB NOT NULL,
              config TEXT NOT NULL, state TEXT NOT NULL, token TEXT, lease_until REAL,
              result TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS events(
              event_id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER NOT NULL,
              kind TEXT NOT NULL, detail TEXT, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE INDEX IF NOT EXISTS work_state ON attempts(state,lease_until);
            ''')

    @contextlib.contextmanager
    def connection(self):
        conn=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        conn.row_factory=sqlite3.Row
        conn.execute('PRAGMA synchronous=FULL')
        try:yield conn
        finally:conn.close()

    @contextlib.contextmanager
    def transaction(self):
        with self.connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                yield conn
                conn.commit()
            except BaseException:
                conn.rollback();raise

    def _register(self,conn,document_id,raw,config,force):
        digest=sha(raw)
        prior=conn.execute('SELECT a.* FROM documents d JOIN attempts a ON a.attempt_id=d.current_attempt WHERE d.document_id=?',(document_id,)).fetchone()
        if prior and not force and prior['source_sha256']==digest and prior['config_key']==config.key:
            return None
        cursor=conn.execute('INSERT INTO attempts(document_id,source_sha256,config_key,raw,config,state) VALUES(?,?,?,?,?,?)',
                            (document_id,digest,config.key,raw,dump(config.as_dict()),'pending'))
        attempt=cursor.lastrowid
        conn.execute('INSERT INTO documents VALUES(?,?) ON CONFLICT(document_id) DO UPDATE SET current_attempt=excluded.current_attempt',(document_id,attempt))
        conn.execute('INSERT INTO events(attempt_id,kind) VALUES(?,?)',(attempt,'enqueued'))
        return attempt

    def ingest(self,paths,config,force=False):
        # Original bytes are persisted before decoding, so malformed exports become per-document errors.
        count=0
        for path in paths:
            path=Path(path)
            raw=path.read_bytes()
            with self.transaction() as conn:
                if self._register(conn,path.name,raw,config,force):count+=1
        return count

    def retry(self,document_id):
        with self.transaction() as conn:
            row=conn.execute('SELECT a.* FROM documents d JOIN attempts a ON a.attempt_id=d.current_attempt WHERE d.document_id=?',(document_id,)).fetchone()
            if row is None:raise ValueError('Unknown document_id')
            return self._register(conn,document_id,row['raw'],Config(**json.loads(row['config'])),True)

    def claim(self,lease=300):
        with self.transaction() as conn:
            now=time.time()
            row=conn.execute("SELECT * FROM attempts WHERE state='pending' OR (state='running' AND lease_until<?) ORDER BY attempt_id LIMIT 1",(now,)).fetchone()
            if not row:return None
            token=uuid.uuid4().hex
            # Read persisted config to use a sufficient lease even when the resume process has new flags.
            cfg=Config(**json.loads(row['config']))
            seconds=lease if lease!=300 else cfg.lease_seconds
            conn.execute("UPDATE attempts SET state='running',token=?,lease_until=? WHERE attempt_id=?",(token,now+seconds,row['attempt_id']))
            conn.execute('INSERT INTO events(attempt_id,kind,detail) VALUES(?,?,?)',(row['attempt_id'],'claimed',token))
            result=dict(row);result.update(token=token,state='running',lease_until=now+seconds)
            return result

    def finish(self,attempt_id,token,result):
        with self.transaction() as conn:
            changed=conn.execute("UPDATE attempts SET state='completed',result=?,lease_until=NULL WHERE attempt_id=? AND token=? AND state='running' AND lease_until>=?",(dump(result),attempt_id,token,time.time())).rowcount
            if changed:conn.execute('INSERT INTO events(attempt_id,kind) VALUES(?,?)',(attempt_id,'completed'))
            return bool(changed)

    def renew(self,attempt_id,token,lease):
        with self.transaction() as conn:
            now=time.time()
            return bool(conn.execute("UPDATE attempts SET lease_until=? WHERE attempt_id=? AND token=? AND state='running' AND lease_until>=?",
                                     (now+lease,attempt_id,token,now)).rowcount)

    @staticmethod
    def record(row):
        r={k:row[k] for k in ('attempt_id','document_id','source_sha256','config_key','state','created_at')}
        cfg=json.loads(row['config'])
        r.update(policy_sha256=sha(cfg['policy'].encode()),model=cfg['model'],provider=cfg['provider'])
        r['configuration']={k:cfg[k] for k in ('timeout','retries','interval','max_output_tokens')}
        r['configuration'].update(prompt_sha256=sha(cfg['prompt'].encode()),
                                  schema_sha256=sha(dump(cfg['schema']).encode()))
        result=json.loads(row['result']) if row['result'] else {
            'extraction':None,'status':row['state'],'owner':'IT Service Desk',
            'next_action':'resume-intake','error':None,
            'response_source':'mock' if cfg['provider']=='mock' else cfg['provider']+'/'+cfg['model']}
        r.update(result)
        if row['state']=='running':r['lease_until']=row['lease_until']
        return r

    def current(self):
        with self.connection() as conn:
            return [self.record(r) for r in conn.execute('SELECT a.* FROM documents d JOIN attempts a ON a.attempt_id=d.current_attempt ORDER BY d.document_id')]

    def history(self,document_id=None):
        with self.connection() as conn:
            rows=conn.execute('SELECT * FROM attempts'+(' WHERE document_id=?' if document_id else '')+' ORDER BY attempt_id',(document_id,) if document_id else ())
            return [self.record(r) for r in rows]

    def snapshot(self):
        with self.connection() as conn:
            conn.execute('BEGIN')
            current=[self.record(r) for r in conn.execute('SELECT a.* FROM documents d JOIN attempts a ON a.attempt_id=d.current_attempt ORDER BY d.document_id')]
            history=[self.record(r) for r in conn.execute('SELECT * FROM attempts ORDER BY attempt_id')]
            conn.commit()
            return current,history

    def event_count(self,kind):
        with self.connection() as conn:return conn.execute('SELECT COUNT(*) FROM events WHERE kind=?',(kind,)).fetchone()[0]


class RateLimiter:
    def __init__(self):
        self.lock=threading.Lock();self.next=0.

    def wait(self,interval):
        with self.lock:
            now=time.monotonic();delay=max(0,self.next-now);self.next=max(now,self.next)+interval
        if delay:time.sleep(delay)


def process(store,workers=4,provider_factory=None):
    if not 1<=workers<=32:raise ValueError('workers must be 1..32')
    limiter=RateLimiter()
    stopping=threading.Event()
    def worker():
        while not stopping.is_set():
            job=store.claim()
            if job is None:return
            cfg=Config(**json.loads(job['config']))
            response_source='mock' if cfg.provider=='mock' else cfg.provider+'/'+cfg.model
            settled=threading.Event()
            def heartbeat():
                while not settled.wait(min(cfg.lease_seconds/3,30)):
                    if not store.renew(job['attempt_id'],job['token'],cfg.lease_seconds):return
            keeper=threading.Thread(target=heartbeat,daemon=True)
            keeper.start()
            try:
                obj=json.loads(job['raw'].decode('utf-8'))
                if not isinstance(obj,dict) or not isinstance(obj.get('message'),str):
                    raise ProviderError('Export requires a message string; correct the source file then re-intake')
                if provider_factory:
                    provider=provider_factory(cfg)
                elif cfg.provider=='mock':
                    provider=MockProvider(cfg)
                elif cfg.provider=='openai':
                    provider=OpenAIProvider(cfg)
                else:
                    raise ProviderError('No adapter configured for saved provider; supply its adapter or re-intake with --provider mock or openai')
                if cfg.provider!='mock':limiter.wait(cfg.interval)
                reply=provider.extract(job['document_id'],obj['message'])
                if cfg.provider=='openai' and isinstance(reply,dict) and isinstance(reply.get('model'),str):
                    response_source='openai/'+reply['model']
                ext=validate_reply(reply,obj['message'],cfg.schema)
                status,owner,next_action=route(ext,obj['message'],job['document_id'])
                result={'extraction':ext,'status':status,'owner':owner,'next_action':next_action,'error':None,'response_source':response_source}
            except Exception as exc:
                message=str(exc) if isinstance(exc,ProviderError) else 'Invalid export or unexpected processing error; inspect source/configuration then retry'
                result={'extraction':None,'status':'error','owner':'IT Service Desk','next_action':'retry-extraction','error':message,'response_source':response_source}
            finally:
                settled.set()
                keeper.join()
            store.finish(job['attempt_id'],job['token'],result)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        try:
            for future in [pool.submit(worker) for _ in range(workers)]:future.result()
        except BaseException:
            stopping.set()
            raise


def atomic_write(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.'+uuid.uuid4().hex)
    with temporary.open('wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def export_records(store,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with (out/'.export.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current,history=store.snapshot()
        queue=[{k:r[k] for k in ('document_id','source_sha256','attempt_id','config_key','state','status','owner','next_action','error','response_source')} for r in current]
        content={'extractions.jsonl':''.join(dump(r)+'\n' for r in current).encode(),
                 'queue.json':(json.dumps(queue,indent=2)+'\n').encode(),
                 'history.jsonl':''.join(dump(r)+'\n' for r in history).encode()}
        generation='snapshots/'+uuid.uuid4().hex
        for name,raw in content.items():
            atomic_write(out/generation/name,raw)
            atomic_write(out/name,raw)
        manifest={'generation':generation,'files':{name:sha(raw) for name,raw in content.items()}}
        atomic_write(out/'snapshot.json',(json.dumps(manifest,indent=2)+'\n').encode())
        return manifest


def accuracy(records,truth):
    indexed={r['document_id']:r for r in records}
    report={'scalar_total':len(truth)*len(SCALARS),'scalar_matches':0,
            'routing_total':len(truth)*3,'routing_matches':0,'differences':[],
            'response_sources':sorted(set(r['response_source'] for r in records))}
    for name,expected in truth.items():
        actual=indexed.get(name,{})
        for field in SCALARS:
            target=expected['expected'][field]
            ext=actual.get('extraction')
            # Missing record/error is always a mismatch, including expected nulls.
            equal=isinstance(ext,dict) and field in ext and ext[field]==target
            if equal:report['scalar_matches']+=1
            else:report['differences'].append({'document_id':name,'field':field,'expected':target,
                'actual':ext.get(field) if isinstance(ext,dict) else '<missing extraction>',
                'evidence':expected['evidence'].get(field,expected['evidence']['unresolved_and_policy_context'])})
        for field,target in expected['route'].items():
            if actual.get(field)==target:report['routing_matches']+=1
            else:report['differences'].append({'document_id':name,'field':field,'expected':target,'actual':actual.get(field)})
    return report


def write_accuracy(records,output):
    truth=json.loads((ROOT/'tests/ground_truth.json').read_text())
    report=accuracy(records,truth)
    text='''# Accuracy procedure and observed comparison\n\nExpected values were frozen from message text and office policy in `tests/ground_truth.json` before implementation. The evidence mapping contains exact source substrings for every non-null scalar, plus the full message for missing/conflicting facts. All 20 supplied documents and the authored `examples/requests/SYN-001.json` are covered. `kind` is normalized from the quoted request wording. These labels and saved replies were manually authored; matching mock labels is a pipeline check, not evidence of live language-model accuracy.\n\nCompare 12 scalar fields per document using literal Python equality, including nulls. Denominator: 21 × 12 = 252. Missing/error records count as 12 mismatches, even when an expected field is null. Compare status/owner/next_action separately: 21 × 3 = 63. Purpose uses a frozen verbatim span: semantically equivalent wording still differs under exact matching. Supporting_quotes and issues are excluded from scalar counts because their wording/selection varies; automated checks enforce exact evidence substrings, null issues, and routing, and reviewers inspect factual coverage.\n\nEach difference below is an exact-match difference with source evidence where applicable; a human must distinguish unsupported facts from equivalent wording. Review every claimed fact against decoded message text; count unsupported/wrong facts separately from omissions, report affected documents/fields, and retain the compared input hashes and configuration keys in extraction records. This comparison alone does not establish a live factual-error rate.\n\nCommands: see README. Use `accuracy` against exported JSONL (plus the synthetic export); changing labels to fit outputs is prohibited. Provider/model/configuration and the recorded response path are stored in each extraction. Request configuration is in `request-evidence.json`.\n\n'''
    text+=f"Observed scalar matches: {report['scalar_matches']}/{report['scalar_total']}. Routing matches: {report['routing_matches']}/{report['routing_total']}. Sources: {', '.join(report['response_sources'])}. Provider labels identify the response path; they do not establish whether transport was live or faked.\n\n"
    text+='## Differences\n\n'+('No exact-match discrepancies observed in these records. Factual review of source evidence remains separate.\n' if not report['differences'] else '```json\n'+json.dumps(report['differences'],indent=2)+'\n```\n')
    text+='\n## Observed configuration and provenance\n\n| Document | Provider / configured model / response source | Source SHA-256 | Configuration key | Settings |\n|---|---|---|---|---|\n'
    for record in sorted(records,key=lambda r:r['document_id']):
        text+=f"| {record['document_id']} | {record.get('provider','unrecorded')} / {record.get('model','unrecorded')} / {record['response_source']} | {record.get('source_sha256','unrecorded')} | {record.get('config_key','unrecorded')} | `{dump(record.get('configuration',{}))}` |\n"
    text+='\n## Frozen source-derived expected fields\n\n| Document | Expected scalars | Status / owner / next action | Evidence |\n|---|---|---|---|\n'
    for name,item in truth.items():
        text+=f"| {name} | `{json.dumps({k:item['expected'][k] for k in SCALARS},ensure_ascii=False)}` | {' / '.join(item['route'].values())} | `{item['source']}`; per-field source quotes in `tests/ground_truth.json` |\n"
    atomic_write(output,text.encode())
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description='Prepare Northstar access requests for human review')
    parser.add_argument('--db',default='.state/intake.db')
    parser.add_argument('--provider',choices=('mock','openai'),default='mock')
    parser.add_argument('--model',default='gpt-4.1-mini')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--timeout',type=float,default=30)
    parser.add_argument('--retries',type=int,default=2)
    parser.add_argument('--interval',type=float,default=.1,help='minimum seconds between live starts in this process')
    parser.add_argument('--max-output-tokens',type=int,default=3000)
    parser.add_argument('--mock-dir',default=str(ROOT/'tests/mock_responses'))
    sub=parser.add_subparsers(dest='command',required=True)
    intake=sub.add_parser('intake');intake.add_argument('paths',nargs='+');intake.add_argument('--enqueue-only',action='store_true');intake.add_argument('--force',action='store_true')
    queue=sub.add_parser('queue');queue.add_argument('--json',action='store_true')
    sub.add_parser('resume')
    retry=sub.add_parser('retry');retry.add_argument('document_id')
    hist=sub.add_parser('history');hist.add_argument('document_id',nargs='?')
    export=sub.add_parser('export');export.add_argument('--out',default='deliverables')
    acc=sub.add_parser('accuracy');acc.add_argument('--records',nargs='+',default=['deliverables/extractions.jsonl','deliverables/synthetic/extractions.jsonl']);acc.add_argument('--out',default='deliverables/accuracy.md')
    evidence=sub.add_parser('request-evidence');evidence.add_argument('--out',default='deliverables/request-evidence.json')
    args=parser.parse_args(argv)
    try:
        if not 1<=args.workers<=32:raise ValueError('workers must be 1..32')
        config=Config(provider=args.provider,model=args.model,timeout=args.timeout,retries=args.retries,
                      interval=args.interval,max_output_tokens=args.max_output_tokens,mock_dir=args.mock_dir)
        store=Store(args.db)
        if args.command=='intake':
            paths=[]
            for item in args.paths:
                path=Path(item)
                paths.extend(sorted(path.glob('*.json')) if path.is_dir() else [path])
            if not paths:raise ValueError('No JSON exports found')
            count=store.ingest(paths,config,force=args.force)
            print(f'Enqueued {count} new attempts ({len(paths)-count} unchanged).',flush=True)
            if not args.enqueue_only:process(store,args.workers)
        elif args.command=='resume':process(store,args.workers)
        elif args.command=='retry':
            attempt=store.retry(args.document_id)
            print(f'Enqueued retry attempt {attempt}. Run: python3 -m access_intake --db {args.db} resume')
        elif args.command=='queue':
            rows=store.current()
            if args.json:print(json.dumps(rows,indent=2))
            else:
                print('DOCUMENT       STATE       STATUS              OWNER             NEXT ACTION')
                for r in rows:print(f"{r['document_id']:14} {r['state']:11} {r['status']:19} {r['owner']:17} {r['next_action']}"+(f"\n  {r['error']}" if r['error'] else ''))
        elif args.command=='history':print(json.dumps(store.history(args.document_id),indent=2))
        elif args.command=='export':print(json.dumps(export_records(store,args.out),indent=2))
        elif args.command=='accuracy':
            records=[json.loads(line) for file in args.records for line in Path(file).read_text().splitlines() if line.strip()]
            report=write_accuracy(records,args.out)
            print(f"Scalars {report['scalar_matches']}/{report['scalar_total']}; routing {report['routing_matches']}/{report['routing_total']}; {len(report['differences'])} differences")
            return 1 if report['differences'] else 0
        elif args.command=='request-evidence':
            message=json.loads((ROOT/'materials/requests/IT-001.json').read_text())['message']
            data={'example_only':True,'live_request_observed':False,'url':OpenAIProvider.endpoint,
                  'method':'POST','headers':{'Authorization':'Bearer <REDACTED>','Content-Type':'application/json'},
                  'body':OpenAIProvider(config).request(message),'timeout_seconds':config.timeout,
                  'max_retries':config.retries,'retryable':'429, 5xx, connection/timeouts; bounded exponential delay and Retry-After capped at 30 seconds',
                  'handling':'Require completed response and message; reject refusal, malformed JSON, missing/extra/type/enum/date errors and non-source quotes. Failures become null extraction and retry-extraction. See access_intake/app.py validate_reply and process.',
                  'documentation':['https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses','https://developers.openai.com/api/reference/resources/responses/methods/create']}
            atomic_write(args.out,(json.dumps(data,indent=2)+'\n').encode())
        return 0
    except KeyboardInterrupt:
        print('Interrupted. Completed work is saved; resume after active leases expire.',file=sys.stderr)
        return 130
    except (ValueError,OSError,sqlite3.Error,ProviderError) as exc:
        # Do not dump exceptions from provider or source payloads into logs.
        print('Command failed: '+(str(exc) if isinstance(exc,(ValueError,ProviderError)) else type(exc).__name__)+'. See README for recovery.',file=sys.stderr)
        return 2
