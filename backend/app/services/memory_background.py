"""Durable post-reply memory extraction. SQL remains the only memory authority."""
import hashlib
import json
import logging
import time
import threading
from uuid import uuid4
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.memory import MemoryJob, ShoppingMemory
from app.services.memory_service import MemoryService


class AutomaticRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Literal['user', 'feedback', 'project', 'reference']
    domain: Literal['shopping', 'aftersales', 'communication']
    key: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)
    source_quote: str = Field(min_length=1, max_length=4000)
    scope: Literal['durable', 'current']
    reference_url: str | None = Field(default=None, max_length=2000)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    records: list[AutomaticRecord] = Field(max_length=10)


class DreamRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')
    memory_id: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=2000)


class DreamResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    records: list[DreamRecord] = Field(max_length=50)


def _versions(db, owner_id):
    return {row.memory_id: {'revision': row.revision, 'key': row.key} for row in db.scalars(
        select(ShoppingMemory).where(ShoppingMemory.owner_id == owner_id)
        .order_by(ShoppingMemory.memory_id))}


def _explicit_version(db, owner_id):
    # Tombstones remain in SQL. Every explicit insert/update/delete increases
    # this aggregate, including equal-clock edits and automatic→explicit edits.
    count, revisions = db.execute(select(func.count(), func.coalesce(func.sum(ShoppingMemory.revision), 0))
        .where(ShoppingMemory.owner_id == owner_id, ShoppingMemory.source == 'explicit')).one()
    return [count, revisions]


def enqueue_extraction(db, *, owner_id, role, source_id, source_text):
    """Called only inside the caller's successful canonical reply transaction."""
    existing = db.scalar(select(MemoryJob).where(MemoryJob.owner_id == owner_id,
        MemoryJob.kind == 'extract', MemoryJob.source_id == source_id))
    if existing is not None:
        return existing.job_id
    job = MemoryJob(job_id='memory-job-' + uuid4().hex, owner_id=owner_id, kind='extract',
        source_id=source_id, source_json=json.dumps({'role':role, 'text':source_text}, ensure_ascii=False),
        versions_json=json.dumps({'rows':_versions(db, owner_id), 'explicit':_explicit_version(db, owner_id)}), status='pending', created_at=time.time())
    db.add(job)
    db.flush()
    return job.job_id


class MemoryWorker:
    def __init__(self, bind, *, extract=None, dream=None, clock=time.time):
        self.bind, self.clock = bind, clock
        self._stop = threading.Event()
        self._thread = None
        if extract is None:
            from app.services.memory_model import extract_memory
            extract = extract_memory
        if dream is None:
            from app.services.memory_model import dream_memory
            dream = dream_memory
        self.extract, self.dream = extract, dream

    def start(self):
        self._thread = threading.Thread(target=self._run, name='memory-background', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=25)

    def _run(self):
        while not self._stop.is_set():
            try:
                if not self.run_once():
                    self._stop.wait(0.5)
            except SQLAlchemyError as error:
                # SQL failures leave pending work/leases durable for recovery.
                logging.getLogger(__name__).warning('Memory SQL recovery pending: %s', type(error).__name__)
                self._stop.wait(1)

    def run_once(self):
        token = uuid4().hex
        with Session(self.bind) as db:
            db.execute(text('BEGIN IMMEDIATE'))
            job = db.scalar(select(MemoryJob).where(
                (MemoryJob.status == 'pending') | ((MemoryJob.status == 'running') & (MemoryJob.lease_until <= self.clock()))
            ).order_by(MemoryJob.created_at, MemoryJob.job_id).limit(1))
            if job is None:
                self._schedule_dream(db)
                job = db.scalar(select(MemoryJob).where(MemoryJob.status == 'pending')
                    .order_by(MemoryJob.created_at, MemoryJob.job_id).limit(1))
            if job is None:
                return False
            job.status, job.lease_token, job.lease_until = 'running', token, self.clock() + 60
            job_id, kind = job.job_id, job.kind
            source, versions = json.loads(job.source_json), json.loads(job.versions_json)
            if not self._source_current(db, job, source, versions):
                job.status, job.error_code, job.lease_until = 'failed', 'MEMORY_SOURCE_SUPERSEDED', None
                db.commit()
                return True
            db.commit()
        if kind == 'extract' and len(source['text']) > 8000:
            self._record_error(job_id, token, 'MEMORY_SOURCE_TOO_LONG')
            return True  # never extract a prefix that might omit a correction
        try:
            output = self.extract(source) if kind == 'extract' else self.dream(source)
        except Exception as error:
            # Model transport is an external boundary. Persist only its class,
            # never provider text that could contain credentials or user data.
            self._record_error(job_id, token, 'MEMORY_MODEL_FAILED:' + type(error).__name__)
            return True
        try:
            result = (ExtractionResult.model_validate(output) if kind == 'extract'
                      else DreamResult.model_validate(output))
        except ValidationError as error:
            self._record_error(job_id, token, 'MEMORY_RESULT_INVALID:' + type(error).__name__)
            return True
        if self._stop.is_set():
            return True  # retain durable running lease for restart recovery
        try:
            with Session(self.bind) as db:
                db.execute(text('BEGIN IMMEDIATE'))
                job = db.get(MemoryJob, job_id)
                if job.status != 'running' or job.lease_token != token or job.lease_until <= self.clock():
                    return True
                if json.loads(job.source_json) != source or json.loads(job.versions_json) != versions:
                    job.status, job.error_code, job.lease_until = 'failed', 'MEMORY_SOURCE_CHANGED', None
                    db.commit()
                    return True
                if not self._source_current(db, job, source, versions):
                    job.status, job.error_code, job.lease_until = 'failed', 'MEMORY_SOURCE_SUPERSEDED', None
                    db.commit()
                    return True
                for candidate in result.records:
                    if kind == 'extract':
                        self._save_candidate(db, job, candidate, source, versions['rows'])
                    else:
                        self._save_dream(db, job, candidate, source, versions['rows'])
                job.status, job.completed_at, job.lease_until = 'completed', self.clock(), None
                job.error_code = None
                db.commit()
        except SQLAlchemyError as error:
            self._record_error(job_id, token, 'MEMORY_PUBLICATION_FAILED:' + type(error).__name__, retryable=True)
            raise  # preserve the original SQL failure; unfinished work remains recoverable
        return True

    def _source_current(self, db, job, source, versions):
        if _explicit_version(db, job.owner_id) != versions['explicit']:
            return False
        if job.kind == 'dream':
            effective = {row['memory_id']:row for row in MemoryService(db, job.owner_id).effective_automatic(self.clock())}
            return len(effective) >= 10 and all(row['memory_id'] in effective
                       and effective[row['memory_id']]['revision'] == versions['rows'][row['memory_id']]['revision']
                       for row in source['records'])
        return True

    def _record_error(self, job_id, token, code, *, retryable=False):
        with Session(self.bind) as db:
            db.execute(text('BEGIN IMMEDIATE'))
            job = db.get(MemoryJob, job_id)
            if job.status == 'running' and job.lease_token == token:
                job.error_code = code
                if not retryable:
                    job.status, job.lease_until = 'failed', None
                db.commit()

    def _schedule_dream(self, db):
        now = self.clock()
        owners = db.scalars(select(ShoppingMemory.owner_id).where(
            ShoppingMemory.source == 'automatic', ShoppingMemory.deleted_at.is_(None),
            ShoppingMemory.expires_at > now).distinct())
        for owner_id in owners:
            effective = MemoryService(db, owner_id).effective_automatic(now)
            if len(effective) < 10:
                continue
            active = db.scalar(select(MemoryJob.job_id).where(MemoryJob.owner_id == owner_id,
                MemoryJob.kind == 'dream', MemoryJob.status.in_(('pending','running'))))
            if active is not None:
                continue
            last_success = db.scalar(select(MemoryJob).where(
                MemoryJob.owner_id == owner_id, MemoryJob.kind == 'dream', MemoryJob.status == 'completed')
                .order_by(MemoryJob.completed_at.desc(), MemoryJob.job_id.desc()).limit(1))
            if last_success is not None and now - last_success.completed_at < 86400:
                continue
            rows = sorted(effective, key=lambda row: (row['updated_at'], row['memory_id']))[:50]
            records, versions = [], {}
            for row in rows:
                record = {name:row[name] for name in ('memory_id','category','domain','key',
                    'content','source_quote','reference_url')}
                if len(json.dumps([*records,record],ensure_ascii=False)) > 20000:
                    break
                records.append(record)
                versions[row['memory_id']] = {'revision':row['revision'],'key':row['key']}
            versions = {'rows':versions, 'explicit':_explicit_version(db, owner_id)}
            source = json.dumps({'records':records},ensure_ascii=False)
            # The same unchanged failed input is not retried in a tight loop.
            previous_success_id = last_success.job_id if last_success is not None else 'initial'
            digest = hashlib.sha256((source + json.dumps(versions,sort_keys=True) + previous_success_id).encode()).hexdigest()
            if db.scalar(select(MemoryJob.job_id).where(MemoryJob.owner_id == owner_id,
                    MemoryJob.kind == 'dream', MemoryJob.source_id == digest)):
                continue
            db.add(MemoryJob(job_id='memory-job-' + uuid4().hex, owner_id=owner_id, kind='dream',
                source_id=digest, source_json=source, versions_json=json.dumps(versions),
                status='pending',created_at=now))
            db.flush()

    def _save_dream(self, db, job, candidate, source, versions):
        original = next((row for row in source['records'] if row['memory_id'] == candidate.memory_id), None)
        if original is None:
            return
        row = db.get(ShoppingMemory, candidate.memory_id)
        if (row is None or row.owner_id != job.owner_id or row.source != 'automatic'
                or row.deleted_at is not None or row.expires_at <= self.clock()
                or row.revision != versions[candidate.memory_id]['revision']):
            return
        siblings = db.scalars(select(ShoppingMemory).where(ShoppingMemory.owner_id == job.owner_id,
            ShoppingMemory.key == row.key))
        if any(other.source == 'explicit' or other.deleted_at is not None for other in siblings):
            return
        if row.content != candidate.content:
            row.content, row.revision, row.updated_at = candidate.content, row.revision + 1, self.clock()
            # Dream does not change source evidence or extend expiry.

    def _save_candidate(self, db, job, candidate, source, versions):
        if candidate.scope != 'durable' or candidate.source_quote not in source['text']:
            return
        if candidate.key in ('budget_fen', 'people'):
            return
        if candidate.reference_url is not None and candidate.reference_url not in source['text']:
            return
        if candidate.category == 'reference' and candidate.reference_url is None:
            return
        if candidate.domain not in ('communication', 'shopping' if source['role'] == 'keke' else 'aftersales'):
            return
        rows = list(db.scalars(select(ShoppingMemory).where(
            ShoppingMemory.owner_id == job.owner_id, ShoppingMemory.key == candidate.key)))
        # All explicit writes and all tombstones fence automatic replacement.
        if any(row.source == 'explicit' or row.deleted_at is not None for row in rows):
            return
        current = {row.memory_id: {'revision':row.revision,'key':row.key} for row in rows}
        captured = {key:value for key,value in versions.items() if value['key'] == candidate.key}
        if current != captured:
            return
        now = self.clock()
        if rows:
            row = max(rows, key=lambda row: (row.updated_at,row.memory_id))
            if row.domain != candidate.domain or row.category != candidate.category:
                return  # a model-chosen key cannot move facts across role/category boundaries
            if row.expires_at is not None and row.expires_at <= now:
                return
            if row.content == candidate.content:
                return  # unchanged content does not renew its original TTL
            row.content, row.revision, row.updated_at = candidate.content, row.revision + 1, now
            row.source_id, row.source_quote = job.source_id, candidate.source_quote
            row.origin_role = source['role']
            row.reference_url = candidate.reference_url
        else:
            db.add(ShoppingMemory(memory_id='memory-' + uuid4().hex, owner_id=job.owner_id,
                category=candidate.category, domain=candidate.domain, key=candidate.key, content=candidate.content,
                source='automatic', origin_role=source['role'], source_id=job.source_id,
                source_quote=candidate.source_quote, reference_url=candidate.reference_url,
                revision=1, created_at=now, updated_at=now, expires_at=now + 30 * 86400))
            db.flush()
