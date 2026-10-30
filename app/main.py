from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone
from typing import Generator, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./evolutia.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DB_URL = database_url()
engine_options = {"pool_pre_ping": True}
if DB_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Research(Base):
    __tablename__ = "research"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Improvement(Base):
    __tablename__ = "improvements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="proposed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


Base.metadata.create_all(bind=engine)


class ResearchCreate(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    context: Optional[str] = Field(default=None, max_length=10000)


class ImprovementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=10000)


class ResearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question: str
    context: Optional[str]
    status: str
    created_at: datetime


class ImprovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]


class StatusOut(BaseModel):
    name: str
    version: str
    status: str
    description: str


app = FastAPI(
    title="EVOLUTIA AI",
    version="0.3.0",
    description="Plataforma experimental de pesquisa e propostas de melhoria com supervisão humana.",
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(authorization: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("EVOLUTIA_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A chave administrativa não foi configurada no servidor.",
        )
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial administrativa inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/", response_model=StatusOut, tags=["Sistema"])
def root() -> StatusOut:
    return StatusOut(
        name="EVOLUTIA AI",
        version=app.version,
        status="online",
        description="API ativa. Alterações de dados exigem autenticação administrativa.",
    )


@app.get("/health", tags=["Sistema"])
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "healthy", "database": "connected", "version": app.version}


@app.post("/research", response_model=ResearchOut, status_code=status.HTTP_201_CREATED, tags=["Pesquisa"])
def create_research(payload: ResearchCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)) -> Research:
    item = Research(question=payload.question.strip(), context=payload.context)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/research", response_model=list[ResearchOut], tags=["Pesquisa"])
def list_research(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)) -> list[Research]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    return list(db.scalars(select(Research).order_by(Research.created_at.desc()).offset(offset).limit(limit)))


@app.post("/improvements", response_model=ImprovementOut, status_code=status.HTTP_201_CREATED, tags=["Melhorias"])
def create_improvement(payload: ImprovementCreate, _: None = Depends(require_admin), db: Session = Depends(get_db)) -> Improvement:
    item = Improvement(title=payload.title.strip(), description=payload.description.strip())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/improvements", response_model=list[ImprovementOut], tags=["Melhorias"])
def list_improvements(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)) -> list[Improvement]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    return list(db.scalars(select(Improvement).order_by(Improvement.created_at.desc()).offset(offset).limit(limit)))


@app.post("/improvements/{improvement_id}/approve", response_model=ImprovementOut, tags=["Melhorias"])
def approve_improvement(improvement_id: int, _: None = Depends(require_admin), db: Session = Depends(get_db)) -> Improvement:
    item = db.get(Improvement, improvement_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")
    if item.status == "approved":
        return item
    item.status = "approved"
    item.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item



class AIAnalysisRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    context: Optional[str] = Field(default=None, max_length=12000)


@app.post("/ai/analyze", tags=["Inteligência Artificial"])
def analyze_with_ai(
    payload: AIAnalysisRequest,
    _: None = Depends(require_admin),
) -> dict:
    """Gera uma análise textual; nunca executa alterações nem publica código."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integração de IA não configurada. Defina OPENAI_API_KEY no ambiente do servidor.",
        )

    model = os.getenv("OPENAI_MODEL", "gpt-5.5").strip() or "gpt-5.5"
    prompt = (
        "Analise a solicitação abaixo para a plataforma EVOLUTIA AI. "
        "Responda em português do Brasil, separando: entendimento do problema, "
        "análise, proposta de melhoria, riscos e próximos passos. "
        "Não afirme que executou ações. Não solicite nem revele segredos. "
        "Toda proposta exige avaliação e aprovação humana antes de qualquer implementação.\n\n"
        f"Pergunta: {payload.question.strip()}\n"
        f"Contexto: {(payload.context or 'Não informado').strip()}"
    )

    try:
        from openai import APIError, OpenAI

        client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        response = client.responses.create(
            model=model,
            instructions=(
                "Você é o módulo de análise da EVOLUTIA AI. "
                "Produza análises úteis, prudentes e verificáveis. "
                "Você não tem permissão para executar código, alterar arquivos ou aprovar propostas."
            ),
            input=prompt,
            max_output_tokens=800,
            store=False,
        )
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço de IA não conseguiu concluir a análise. Verifique a configuração e tente novamente.",
        ) from exc

    return {
        "analysis": response.output_text,
        "model": model,
        "requires_human_review": True,
        "code_execution": False,
    }
