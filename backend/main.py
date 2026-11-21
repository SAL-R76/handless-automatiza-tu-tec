"""Handless · Aplicación académica E4 (solo datos ficticios).
FastAPI + SQLAlchemy; guardas de roles y transiciones en el servidor.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
ROLE_LABELS = {'jefatura':'Jefatura solicitante','coordinacion':'Coordinación de mantenimiento','tecnico':'Personal técnico','planeacion':'Planeación'}
STATUS_LABELS = {'recibida':'Recibida','asignada':'Asignada','en_atencion':'En atención','pendiente_vobo':'Pendiente de Vo.Bo.','retrabajo':'Requiere retrabajo','aprobada':'Vo.Bo. otorgado','cerrada':'Cerrada'}

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(60),unique=True,index=True)
    display: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30))
    passhash: Mapped[str] = mapped_column(String(150))

class Ticket(Base):
    __tablename__='tickets'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(20), default='correctivo')
    area: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(120))
    asset: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    contact: Mapped[str] = mapped_column(String(120))
    priority: Mapped[str] = mapped_column(String(30), default='media')
    category: Mapped[str] = mapped_column(String(60), default='Infraestructura')
    destination: Mapped[str] = mapped_column(String(100), default='Recursos Materiales')
    status: Mapped[str] = mapped_column(String(30), default='recibida')
    route: Mapped[str] = mapped_column(String(20), default='interna')
    external_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    order_number: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    work_notes: Mapped[Optional[str]] = mapped_column(Text,nullable=True)
    vobo_by: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)
    vobo_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text,nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Audit(Base):
    __tablename__='audit'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_role: Mapped[str] = mapped_column(String(30))
    action: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str] = mapped_column(Text, default='')
    new_value: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class Preventive(Base):
    __tablename__='preventive'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    area: Mapped[str] = mapped_column(String(100))
    period: Mapped[str] = mapped_column(String(50))
    findings: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    program_generated: Mapped[bool] = mapped_column(Boolean,default=False)

class UsabilitySurvey(Base):
    __tablename__='usability_surveys'
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    participant_code: Mapped[str] = mapped_column(String(30),unique=True)
    responses: Mapped[str] = mapped_column(Text)
    task_completed: Mapped[bool] = mapped_column(Boolean)
    task_seconds: Mapped[int] = mapped_column(Integer)
    sus_score: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class SusIn(BaseModel):
    participant_code: str=Field(min_length=2,max_length=30)
    responses: list[int]=Field(min_length=10,max_length=10)
    task_completed: bool
    task_seconds: int=Field(ge=0,le=7200)

class LoginIn(BaseModel):
    username: str
    password: str
class CreateTicket(BaseModel):
    area: str = Field(min_length=2,max_length=100)
    location: str = Field(min_length=3,max_length=120)
    asset: str = Field(min_length=2,max_length=100)
    description: str = Field(min_length=10,max_length=2000)
    contact: str = Field(min_length=2,max_length=120)
    category: str = Field(default='Infraestructura',max_length=60)
    kind: str = 'correctivo'
class AssignIn(BaseModel):
    technician_id: int
    priority: str = 'media'
    destination: str = 'Recursos Materiales'
    route: str = 'interna'
    external_reference: Optional[str] = None
class WorkIn(BaseModel):
    note: str = Field(min_length=5,max_length=2000)
    finished: bool = False
class DecisionIn(BaseModel):
    approved: bool
    reason: Optional[str] = None
class PreventiveIn(BaseModel):
    area: str=Field(min_length=2,max_length=100)
    period: str=Field(min_length=4,max_length=50)
    findings: list[str]=Field(min_length=1)


def password_hash(value:str, salt: str|None=None)->str:
    salt=salt or secrets.token_hex(16)
    h=hashlib.pbkdf2_hmac('sha256',value.encode(),bytes.fromhex(salt),220000)
    return f'{salt}:{h.hex()}'
def verify_password(value:str, stored:str)->bool:
    try:
        salt,_=stored.split(':')
        return hmac.compare_digest(password_hash(value,salt),stored)
    except Exception:return False

def make_token(user:User,secret:str)->str:
    payload={'sub':user.id,'role':user.role,'exp':int(time.time())+3600*8}
    raw=base64.urlsafe_b64encode(json.dumps(payload,separators=(',',':')).encode()).rstrip(b'=')
    sig=hmac.new(secret.encode(),raw,hashlib.sha256).digest()
    return raw.decode()+'.'+base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
def parse_token(token:str,secret:str)->int:
    try:
        raw,sig=token.split('.',1)
        braw=raw.encode()
        expected=base64.urlsafe_b64encode(hmac.new(secret.encode(),braw,hashlib.sha256).digest()).rstrip(b'=').decode()
        if not secrets.compare_digest(expected,sig):raise ValueError('firma')
        payload=json.loads(base64.urlsafe_b64decode(raw+'='*(-len(raw)%4)))
        if payload['exp']<time.time():raise ValueError('caducidad')
        return int(payload['sub'])
    except Exception:raise HTTPException(status_code=401,detail='Sesión inválida o caducada')

def stamp()->datetime:return datetime.now(timezone.utc)
def iso(v):return v.isoformat() if v else None

def ticket_out(t:Ticket)->dict:
    return {k: (iso(getattr(t,k)) if k.endswith('_at') else getattr(t,k)) for k in ('id','folio','kind','area','location','asset','description','contact','priority','category','destination','status','route','external_reference','author_id','technician_id','order_number','work_notes','vobo_by','vobo_at','rejection_reason','closed_at','created_at','updated_at')}
def audit_out(a:Audit)->dict:return {'id':a.id,'ticket_id':a.ticket_id,'actor_id':a.actor_id,'actor_role':a.actor_role,'action':a.action,'old_value':a.old_value,'new_value':a.new_value,'created_at':iso(a.created_at)}

def setup_engine(db_url:str):
    if db_url.startswith('postgres://'): db_url='postgresql+psycopg://'+db_url.removeprefix('postgres://')
    elif db_url.startswith('postgresql://'): db_url='postgresql+psycopg://'+db_url.removeprefix('postgresql://')
    opts={'pool_pre_ping':True}
    if db_url.startswith('sqlite'):
        opts['connect_args']={'check_same_thread':False}
        if ':memory:' in db_url:opts['poolclass']=StaticPool
    return create_engine(db_url,**opts)

def create_app(db_url: str|None=None, token_secret: str|None=None)->FastAPI:
    url=db_url or os.environ.get('DATABASE_URL',f'sqlite:///{ROOT / "handless-local.db"}')
    engine=setup_engine(url)
    SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
    Base.metadata.create_all(engine)
    secret=token_secret or os.environ.get('SESSION_SECRET','DEV-SOLO-LOCAL-NO-PRODUCTION')
    if os.environ.get('RENDER') and secret=='DEV-SOLO-LOCAL-NO-PRODUCTION':
        raise RuntimeError('SESSION_SECRET obligatoria para despliegue')
    with SessionLocal() as db:
        if not db.scalar(select(User.id).limit(1)):
            demo_password=os.environ.get('DEMO_PASSWORD','HandlessDemo2026!')
            users=[('jefatura','Jefatura A (ficticia)','jefatura'),('coordinacion','Coordinación B (ficticia)','coordinacion'),('tecnico','Técnico C (ficticio)','tecnico'),('planeacion','Planeación D (ficticia)','planeacion')]
            for username,display,role in users:
                db.add(User(username=username,display=display,role=role,passhash=password_hash(demo_password)))
            db.commit()
    app=FastAPI(title='Handless API · E4',description='Sistema académico con datos ficticios. No es instalación institucional.',version='1.0.0')
    app.state.db=SessionLocal
    def get_db():
        with SessionLocal() as db:yield db
    def actor(authorization:Annotated[str|None,Header()]=None,db:Session=Depends(get_db)):
        if not authorization or not authorization.lower().startswith('bearer '):raise HTTPException(401,'Inicia sesión')
        uid=parse_token(authorization[7:].strip(),secret)
        user=db.get(User,uid)
        if not user:raise HTTPException(401,'Usuario no disponible')
        return user
    def allow(user:User,*roles):
        if user.role not in roles:raise HTTPException(status_code=403,detail='Acción no permitida para este rol')
    def visible(db:Session,user:User):
        q=select(Ticket)
        if user.role=='jefatura':q=q.where(Ticket.author_id==user.id)
        elif user.role=='tecnico':q=q.where(Ticket.technician_id==user.id)
        elif user.role=='planeacion':q=q.where(Ticket.status=='cerrada')
        return q
    def ticket_for(db:Session,user:User,id:int)->Ticket:
        t=db.get(Ticket,id)
        if not t:raise HTTPException(404,'Folio no encontrado')
        allowed=user.role=='coordinacion' or (user.role=='jefatura' and user.id==t.author_id) or (user.role=='tecnico' and user.id==t.technician_id) or (user.role=='planeacion' and t.status=='cerrada')
        if not allowed:raise HTTPException(404,'Folio no encontrado')
        return t
    def audit(db:Session,t:Ticket,user:User,action:str,old:str,new:str):
        db.add(Audit(ticket_id=t.id,actor_id=user.id,actor_role=user.role,action=action,old_value=old,new_value=new))
        t.updated_at=stamp()
    @app.get('/api/health')
    def health():return {'status':'ok','app':'handless-e4','environment':'academic-demo'}
    @app.post('/api/login')
    def login(inp:LoginIn,db:Session=Depends(get_db)):
        user=db.scalar(select(User).where(User.username==inp.username))
        if not user or not verify_password(inp.password,user.passhash):raise HTTPException(401,'Credenciales incorrectas')
        return {'token':make_token(user,secret),'user':{'id':user.id,'username':user.username,'display':user.display,'role':user.role}}
    @app.get('/api/me')
    def me(user:User=Depends(actor)):
        return {'id':user.id,'username':user.username,'display':user.display,'role':user.role}
    @app.get('/api/users')
    def users(db:Session=Depends(get_db),user:User=Depends(actor)):
        return [{'id':u.id,'display':u.display,'role':u.role} for u in db.scalars(select(User).order_by(User.id))]
    @app.get('/api/tickets')
    def list_tickets(q:str='',status:str='',kind:str='',db:Session=Depends(get_db),user:User=Depends(actor)):
        stmt=visible(db,user)
        if q:
            stmt=stmt.where(Ticket.folio.ilike(f'%{q}%') | Ticket.asset.ilike(f'%{q}%') | Ticket.area.ilike(f'%{q}%'))
        if status:stmt=stmt.where(Ticket.status==status)
        if kind:stmt=stmt.where(Ticket.kind==kind)
        return [ticket_out(t) for t in db.scalars(stmt.order_by(Ticket.id.desc()).limit(300))]
    @app.get('/api/tickets/{id}')
    def get_ticket(id:int,db:Session=Depends(get_db),user:User=Depends(actor)):
        t=ticket_for(db,user,id)
        audits=list(db.scalars(select(Audit).where(Audit.ticket_id==id).order_by(Audit.id.desc())))
        return {'ticket':ticket_out(t),'audit':[audit_out(a) for a in audits]}
    @app.post('/api/tickets',status_code=201)
    def create_ticket(inp:CreateTicket,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'jefatura')
        if inp.kind!='correctivo':raise HTTPException(422,'Usa el módulo de preventivo')
        t=Ticket(folio='PENDIENTE',area=inp.area.strip(),location=inp.location.strip(),asset=inp.asset.strip(),description=inp.description.strip(),contact=inp.contact.strip(),category=inp.category,author_id=user.id)
        db.add(t);db.flush()
        t.folio=f'HLS-2026-{t.id:05d}'
        audit(db,t,user,'crear_solicitud','',t.status)
        db.commit();db.refresh(t)
        return ticket_out(t)
    @app.post('/api/tickets/{id}/assign')
    def assign(id:int,inp:AssignIn,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'coordinacion');t=ticket_for(db,user,id)
        if t.status not in ('recibida','asignada'):raise HTTPException(409,'La orden no puede asignarse en este estado')
        u=db.get(User,inp.technician_id)
        if not u or u.role!='tecnico':raise HTTPException(422,'Selecciona un técnico válido')
        if inp.priority not in ('baja','media','alta','urgente'):raise HTTPException(422,'Prioridad incorrecta')
        if inp.route not in ('interna','externa'):raise HTTPException(422,'Ruta incorrecta')
        if inp.route=='externa' and not inp.external_reference:
            raise HTTPException(422,'Para servicio externo registra la referencia de la autorización institucional (simulada). Handless no realiza compras.')
        old=t.status
        t.technician_id=u.id;t.destination=inp.destination;t.priority=inp.priority;t.route=inp.route
        t.external_reference=inp.external_reference if inp.route=='externa' else None
        t.order_number='OT-'+t.folio;t.status='asignada'
        audit(db,t,user,'asignar_orden',old,t.status+':'+str(u.id));db.commit()
        return ticket_out(t)
    @app.post('/api/tickets/{id}/work')
    def work(id:int,inp:WorkIn,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'tecnico');t=ticket_for(db,user,id)
        if t.status not in ('asignada','en_atencion','retrabajo'):
            raise HTTPException(409,'No se puede intervenir en este estado')
        old=t.status
        t.work_notes=((t.work_notes+'\n') if t.work_notes else '')+f'{stamp().isoformat()} - {inp.note.strip()}'
        t.status='pendiente_vobo' if inp.finished else 'en_atencion'
        t.vobo_by=None;t.vobo_at=None
        audit(db,t,user,'registrar_intervencion',old,t.status);db.commit()
        return ticket_out(t)
    @app.post('/api/tickets/{id}/decision')
    def decision(id:int,inp:DecisionIn,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'jefatura');t=ticket_for(db,user,id)
        if t.status!='pendiente_vobo':raise HTTPException(409,'El trabajo todavía no está listo para validación')
        if not inp.approved and (not inp.reason or len(inp.reason.strip())<4):raise HTTPException(422,'Indica motivo de rechazo')
        old=t.status
        if inp.approved:
            t.vobo_by=user.id;t.vobo_at=stamp();t.rejection_reason=None;t.status='aprobada'
        else:
            t.vobo_by=None;t.vobo_at=None;t.rejection_reason=inp.reason;t.status='retrabajo'
        audit(db,t,user,'validar_vobo' if inp.approved else 'rechazar_servicio',old,t.status)
        db.commit();return ticket_out(t)
    @app.post('/api/tickets/{id}/close')
    def close(id:int,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'coordinacion');t=ticket_for(db,user,id)
        if t.status!='aprobada' or not t.vobo_by or not t.vobo_at:
            raise HTTPException(409,'No se permite cerrar sin visto bueno de jefatura')
        old=t.status;t.status='cerrada';t.closed_at=stamp()
        audit(db,t,user,'cerrar_orden',old,t.status);db.commit()
        return ticket_out(t)
    @app.post('/api/preventive',status_code=201)
    def preventive(inp:PreventiveIn,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'jefatura','coordinacion')
        vals=[x.strip() for x in inp.findings if x.strip()]
        if not vals:raise HTTPException(422,'Registra al menos un hallazgo')
        p=Preventive(owner_id=user.id,area=inp.area,period=inp.period,findings=json.dumps(vals,ensure_ascii=False))
        db.add(p);db.commit();db.refresh(p)
        return {'id':p.id,'format':'TecNM-AD-PO-001-01','area':p.area,'period':p.period,'findings':vals,'program_generated':False}
    @app.get('/api/preventive')
    def preventive_list(db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'jefatura','coordinacion')
        q=select(Preventive)
        if user.role=='jefatura':q=q.where(Preventive.owner_id==user.id)
        return [{'id':p.id,'area':p.area,'period':p.period,'findings':json.loads(p.findings),'program_generated':p.program_generated,'created_at':iso(p.created_at)} for p in db.scalars(q.order_by(Preventive.id.desc()))]
    @app.post('/api/preventive/{id}/program')
    def make_program(id:int,db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'coordinacion')
        p=db.get(Preventive,id)
        if not p:raise HTTPException(404,'Verificación inexistente')
        p.program_generated=True;db.commit()
        return {'format':'TecNM-AD-PO-001-03','verification_id':id,'period':p.period,'area':p.area,'activities':[{'activity':v,'status':'propuesta_sin_aprobar'} for v in json.loads(p.findings)],'warning':'Programa preventivo en borrador; requiere aprobación institucional'}
    @app.get('/api/metrics')
    def metrics(db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'coordinacion','planeacion')
        ts=list(db.scalars(visible(db,user)))
        dur=[(t.closed_at-t.created_at).total_seconds()/3600 for t in ts if t.closed_at and t.created_at]
        by_status={s:len([t for t in ts if t.status==s]) for s in STATUS_LABELS}
        return {'total':len(ts),'closed':by_status['cerrada'],'pending':len(ts)-by_status['cerrada'],'by_status':by_status,'average_resolution_hours':round(sum(dur)/len(dur),2) if dur else None}
    @app.get('/api/exports/closed.csv')
    def export_csv(db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'planeacion','coordinacion')
        output=io.StringIO();writer=csv.writer(output)
        writer.writerow(['Folio','Formato','Área','Ubicación','Activo','Estado','Orden','Fecha cierre','Vo.Bo.','Referencia servicio externo'])
        for t in db.scalars(select(Ticket).where(Ticket.status=='cerrada').order_by(Ticket.id)):
            writer.writerow([t.folio,'TecNM-AD-PO-001-04',t.area,t.location,t.asset,t.status,t.order_number,iso(t.closed_at),iso(t.vobo_at),t.external_reference or ''])
        return Response(content=output.getvalue().encode('utf-8-sig'),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="handless_ordenes_cerradas.csv"'})
    @app.post('/api/sus',status_code=201)
    def submit_sus(inp:SusIn,db:Session=Depends(get_db),user:User=Depends(actor)):
        if any(x<1 or x>5 for x in inp.responses):raise HTTPException(422,'Cada respuesta SUS debe ser 1 a 5')
        code=inp.participant_code.strip().upper()
        if db.scalar(select(UsabilitySurvey.id).where(UsabilitySurvey.participant_code==code)):
            raise HTTPException(409,'Este código de participante ya tiene una encuesta registrada')
        score=2.5*sum((v-1 if i%2==0 else 5-v) for i,v in enumerate(inp.responses))
        db.add(UsabilitySurvey(participant_code=code,responses=json.dumps(inp.responses),task_completed=inp.task_completed,task_seconds=inp.task_seconds,sus_score=score))
        db.commit()
        return {'recorded':True,'participant_code':code,'score':score,'notice':'Resultado de cuestionario aportado por participante. La identidad real no se almacena.'}
    @app.get('/api/sus/summary')
    def sus_summary(db:Session=Depends(get_db),user:User=Depends(actor)):
        allow(user,'coordinacion','planeacion')
        rows=list(db.scalars(select(UsabilitySurvey)))
        return {'participants':len(rows),'required':5,'mean_sus':round(sum(s.sus_score for s in rows)/len(rows),2) if rows else None,
                'completed_within_240_s':sum(s.task_completed and s.task_seconds<=240 for s in rows),
                'individuals':[{'code':s.participant_code,'task_completed':s.task_completed,'task_seconds':s.task_seconds,'sus_score':s.sus_score} for s in rows],
                'complete':len(rows)>=5}
    @app.get('/api/policy')
    def policy(user:User=Depends(actor)):
        return {'document_codes':['TecNM-AD-PO-001-01','TecNM-AD-PO-001-02','TecNM-AD-PO-001-03','TecNM-AD-PO-001-04'],'min_retention_days':365,'automatic_deletion':False,'notice':'Política documentada para el prototipo. Backups y retención efectiva requieren infraestructura administrada.'}
    static_path=ROOT/'frontend'/'dist'
    if static_path.exists():
        app.mount('/assets',StaticFiles(directory=static_path/'assets'),name='assets')
        @app.get('/{path:path}',include_in_schema=False)
        def spa(path:str):
            candidate=static_path/path
            if candidate.is_file() and candidate.resolve().is_relative_to(static_path.resolve()):return FileResponse(candidate)
            return FileResponse(static_path/'index.html')
    return app

app=create_app()
