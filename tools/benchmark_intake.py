#!/usr/bin/env python3
"""Offline repeated-message workload check; no live extraction/throughput claim."""
import argparse
import json
from pathlib import Path
import platform
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from access_intake.app import Config, MockProvider, Store, process


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count',type=int,default=2000)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--out',default='planning/workload.json')
    args=parser.parse_args()
    if args.count<1:parser.error('count must be positive')
    raw=(ROOT/'materials/requests/IT-001.json').read_bytes()
    cfg=Config()
    # Repeat a known fixture under independent filenames, sharing one request ID.
    # This exercises durable scheduling, validation and routing, not novel extraction.
    class RepeatedFixture:
        def __init__(self,config):self.provider=MockProvider(config)
        def extract(self,document_id,message):return self.provider.extract('IT-001.json',message)
    start=time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        paths=[]
        for i in range(args.count):
            p=folder/f'load-{i:05}.json';p.write_bytes(raw);paths.append(p)
        store=Store(folder/'state.db')
        store.ingest(paths,cfg)
        enqueued=time.monotonic()
        process(store,args.workers,provider_factory=RepeatedFixture)
        finished=time.monotonic()
        rows=store.current()
        result={'mode':'mock repeated IT-001 source and saved reply; no live calls',
                'python':platform.python_version(),'count':args.count,'workers':args.workers,
                'enqueue_seconds':round(enqueued-start,3),'processing_seconds':round(finished-enqueued,3),
                'current_count':len(rows),'completed':sum(r['state']=='completed' for r in rows),
                'errors':sum(r['status']=='error' for r in rows),'claims':store.event_count('claimed')}
        assert result['current_count']==result['completed']==result['claims']==args.count,result
        assert result['errors']==0,result
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
