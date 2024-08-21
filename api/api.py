"""Python script to create a FastAPI API that connects to the courts database using SQLAlchemy
allowing the user to filter court cases by various parameters"""

from os import getenv
from typing import List, Optional
from datetime import date
from fastapi import FastAPI, Depends, Query, status, Response, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import relationship, sessionmaker, Session, joinedload, selectinload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv()
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Initialises a new session for each request and close it after"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

Base = declarative_base()
metadata = Base.metadata


class Court(Base):
    """SQLAlchemy declarative mapping for the court table"""

    __tablename__ = "court"
    court_id = Column(Integer, primary_key=True)
    court_name = Column(String(100), nullable=False, unique=True)


class Judge(Base):
    """SQLAlchemy declarative mapping for the judge table"""

    __tablename__ = "judge"
    judge_id = Column(Integer, primary_key=True)
    judge_name = Column(String(200), nullable=False, unique=True)


class LawFirm(Base):
    """SQLAlchemy declarative mapping for the law_firm table"""

    __tablename__ = "law_firm"
    law_firm_id = Column(Integer, primary_key=True)
    law_firm_name = Column(String(255), unique=True)
    lawyers = relationship("Lawyer", back_populates="law_firm")


class Participant(Base):
    """SQLAlchemy declarative mapping for the participant table"""

    __tablename__ = "participant"
    participant_id = Column(Integer, primary_key=True)
    participant_name = Column(String(512), unique=True)


class Tag(Base):
    """SQLAlchemy declarative mapping for the tag table"""

    __tablename__ = "tag"
    tag_id = Column(Integer, primary_key=True)
    tag_name = Column(String(250), nullable=False, unique=True)


class Verdict(Base):
    """SQLAlchemy declarative mapping for the verdict table"""

    __tablename__ = "verdict"
    verdict_id = Column(Integer, primary_key=True)
    verdict = Column(String(50), nullable=False, unique=True)


class CourtCase(Base):
    """SQLAlchemy declarative mapping for the court_case table"""

    __tablename__ = "court_case"
    court_case_id = Column(String(250), primary_key=True)
    summary = Column(Text)
    verdict_id = Column(ForeignKey("verdict.verdict_id"))
    title = Column(String(512))
    court_date = Column(Date)
    case_number = Column(String(250))
    case_url = Column(String(512))
    court_id = Column(ForeignKey("court.court_id"))
    verdict_summary = Column(Text)
    court = relationship("Court")
    verdict = relationship("Verdict")
    tags = relationship("Tag", secondary="tag_assignment")
    judges = relationship("Judge", secondary="judge_assignment")
    participants = relationship("Participant", secondary="participant_assignment")
    participant_assignments = relationship(
        "ParticipantAssignment", back_populates="court_case"
    )


class Lawyer(Base):
    """SQLAlchemy declarative mapping for the lawyer table"""

    __tablename__ = "lawyer"
    __table_args__ = (UniqueConstraint("lawyer_name", "law_firm_id"),)
    lawyer_id = Column(Integer, primary_key=True)
    lawyer_name = Column(String(200))
    law_firm_id = Column(ForeignKey("law_firm.law_firm_id"))
    law_firm = relationship("LawFirm", back_populates="lawyers")


class ParticipantAssignment(Base):
    """SQLAlchemy declarative mapping for the participant_assignment table"""

    __tablename__ = "participant_assignment"
    court_case_id = Column(
        ForeignKey("court_case.court_case_id"), primary_key=True, nullable=False
    )
    participant_id = Column(
        ForeignKey("participant.participant_id"), primary_key=True, nullable=False
    )
    lawyer_id = Column(ForeignKey("lawyer.lawyer_id"))
    is_defendant = Column(Boolean)
    court_case = relationship("CourtCase", back_populates="participant_assignments")
    lawyer = relationship("Lawyer")
    participant = relationship("Participant")

    @hybrid_property
    def participant_name(self):
        """Adds participant_name property to the ParticipantAssignment class"""
        return self.participant.participant_name

    @hybrid_property
    def lawyer_name(self):
        """Adds lawyer_name property to the ParticipantAssignment class"""
        return self.lawyer.lawyer_name

    @hybrid_property
    def law_firm_name(self):
        """Adds law_firm_name property to the ParticipantAssignment class"""
        return self.lawyer.law_firm.law_firm_name


t_judge_assignment = Table(
    "judge_assignment",
    metadata,
    Column(
        "court_case_id",
        ForeignKey("court_case.court_case_id"),
        primary_key=True,
        nullable=False,
    ),
    Column("judge_id", ForeignKey("judge.judge_id"), primary_key=True, nullable=False),
)

t_tag_assignment = Table(
    "tag_assignment",
    metadata,
    Column(
        "court_case_id",
        ForeignKey("court_case.court_case_id"),
        primary_key=True,
        nullable=False,
    ),
    Column("tag_id", ForeignKey("tag.tag_id"), primary_key=True, nullable=False),
)

# PYDANTIC MODELS


class CourtModel(BaseModel):
    """Pydantic model for the court table"""

    court_name: str

    class Config:
        orm_mode = True


class JudgeModel(BaseModel):
    """Pydantic model for the judge table"""

    judge_name: str

    class Config:
        orm_mode = True


class LawFirmModel(BaseModel):
    """Pydantic model for the law_firm table"""

    law_firm_name: Optional[str]

    class Config:
        orm_mode = True


class TagModel(BaseModel):
    """Pydantic model for the tag table"""

    tag_name: str

    class Config:
        orm_mode = True


class VerdictModel(BaseModel):
    """Pydantic model for the verdict table"""

    verdict: str

    class Config:
        orm_mode = True


class LawyerModel(BaseModel):
    """Pydantic model for the lawyer table"""

    lawyer_name: Optional[str]
    law_firm: Optional[LawFirmModel]

    class Config:
        orm_mode = True


class ParticipantAssignmentModel(BaseModel):
    """Pydantic model for the participant_assignment table"""

    is_defendant: Optional[bool]
    participant_name: Optional[str]
    lawyer_name: Optional[str]
    law_firm_name: Optional[str]

    class Config:
        orm_mode = True


class ParticipantAssignmentWithCourtCaseModel(BaseModel):
    """Pydantic model for the participant_assignment table with court_case_id"""

    court_case_id: str
    is_defendant: Optional[bool]
    participant_name: Optional[str]
    lawyer_name: Optional[str]
    law_firm_name: Optional[str]

    class Config:
        orm_mode = True


class CourtCaseModel(BaseModel):
    """Pydantic model for the court_case table"""

    court_case_id: str
    summary: Optional[str]
    title: Optional[str]
    court_date: Optional[date]
    case_number: Optional[str]
    case_url: Optional[str]
    verdict_summary: Optional[str]
    court: Optional[CourtModel]
    verdict: Optional[VerdictModel]
    tags: List[TagModel]
    judges: List[JudgeModel]
    participant_assignments: List[ParticipantAssignmentModel]

    class Config:
        orm_mode = True


def no_matches(response: Response, endpoint: str) -> JSONResponse:
    """Returns a JSON response with a message if no matches are found"""
    response.status_code = status.HTTP_200_OK
    return JSONResponse(
        {"message": f"No matching {endpoint} found matching query parameters."}
    )


def validate_query_params(params: dict, query_param_list: list) -> None:
    unsupported_params = [
        query_param
        for query_param in params.keys()
        if query_param not in query_param_list
    ]

    if unsupported_params:
        raise HTTPException(
            status_code=400,
            detail=f"Query parameter(s) '{', '.join(unsupported_params)}' are not supported. Supported query parameters are {query_param_list}",
        )


@app.get("/")
def get_api_overview() -> JSONResponse:
    return JSONResponse(
        {
            "message": "Welcome to the Justice Lens API",
            "endpoints": {
                "/courts/": "read_courts",
                "/judges/": "read_judges",
                "/lawyers/": "read_lawyers",
                "/law_firms/": "read_law_firms",
                "/participants/": "read_participants",
                "/tags/": "read_tags",
                "/verdicts/": "read_verdicts",
                "/court_cases/": "read_court_cases",
            },
        }
    )


@app.get("/courts/")
def read_courts(
    response: Response,
    request: Request,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    search: Optional[str] = Query(None, description="Court name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get court types with optional search and limit parameters"""

    params = request.query_params
    query_param_list = ["search", "limit"]
    validate_query_params(params, query_param_list)

    query = db.query(Court)
    if search is not None:
        query = query.where(Court.court_name.ilike(f"%{search}%"))

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "court names")
    return result


@app.get("/judges/", response_model=List[JudgeModel])
def read_judges(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    search: Optional[str] = Query(None, description="Judge name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get judge names with optional search and limit parameters"""
    params = request.query_params
    query_param_list = ["search", "limit"]
    validate_query_params(params, query_param_list)

    query = db.query(Judge)
    if search is not None:
        query = query.where(Judge.judge_name.ilike(f"%{search}%"))

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "judge names")

    return result


@app.get("/lawyers/", response_model=List[LawyerModel])
def read_lawyers(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    lawyer: Optional[str] = Query(None, description="Lawyer name to filter by"),
    law_firm: Optional[str] = Query(None, description="Law firm name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get lawyer and law firm names with optional search and limit parameters"""
    params = request.query_params
    query_param_list = ["lawyer", "law_firm", "limit"]
    validate_query_params(params, query_param_list)

    query = db.query(Lawyer).options(selectinload(Lawyer.law_firm))

    if lawyer is not None:
        query = query.where(Lawyer.lawyer_name.ilike(f"%{lawyer}%"))

    if law_firm is not None:
        query = query.join(Lawyer.law_firm).where(
            LawFirm.law_firm_name.ilike(f"%{law_firm}%")
        )

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "lawyer names")

    return query.all()


@app.get("/law_firms/", response_model=List[LawFirmModel])
def read_law_firms(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    search: Optional[str] = Query(None, description="Law firm name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get law firm names with optional search and limit parameters"""
    params = request.query_params
    query_param_list = ["search", "limit"]
    validate_query_params(params, query_param_list)

    query = db.query(LawFirm)
    if search is not None:
        query = query.where(LawFirm.law_firm_name.ilike(f"%{search}%"))

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "law firm names")

    return result


@app.get("/participants/", response_model=List[ParticipantAssignmentWithCourtCaseModel])
def read_participants(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    participant: Optional[str] = Query(
        None, description="Participant name to filter by"
    ),
    lawyer: Optional[str] = Query(None, description="Lawyer name to filter by"),
    law_firm: Optional[str] = Query(None, description="Law firm name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get participant names, lawyer and law firm with optional
    search and limit parameters"""
    params = request.query_params
    query_param_list = ["participant", "lawyer", "law_firm", "limit"]
    validate_query_params(params, query_param_list)

    query = db.query(ParticipantAssignment).options(
        joinedload(ParticipantAssignment.participant),
        joinedload(ParticipantAssignment.lawyer).joinedload(Lawyer.law_firm),
    )

    if participant is not None:
        query = query.join(ParticipantAssignment.participant).where(
            Participant.participant_name.ilike(f"%{participant}%")
        )

    if lawyer is not None:
        query = query.join(ParticipantAssignment.lawyer).where(
            Lawyer.lawyer_name.ilike(f"%{lawyer}%")
        )

    if law_firm is not None:
        query = (
            query.join(ParticipantAssignment.lawyer)
            .join(Lawyer.law_firm)
            .where(LawFirm.law_firm_name.ilike(f"%{law_firm}%"))
        )

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "participants")
    return result


@app.get("/tags/", response_model=List[TagModel])
def read_tags(
    request: Request,
    response: Response,
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    search: Optional[str] = Query(None, description="Tag name to filter by"),
    db: Session = Depends(get_db),
):
    """API endpoint to get tag names with optional search and limit parameters"""
    params = request.query_params
    query_param_list = ["search", "limit"]
    validate_query_params(params, query_param_list)
    query = db.query(Tag)
    if search is not None:
        query = query.where(Tag.tag_name.ilike(f"%{search}%"))

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "tag names")
    return result


@app.get("/verdicts/", response_model=List[VerdictModel])
def read_verdicts(db: Session = Depends(get_db)):
    """API endpoint to get verdicts"""
    query = db.query(Verdict)
    result = query.all()
    return result


@app.get("/court_cases/", response_model=List[CourtCaseModel])
def read_court_cases(
    request: Request,
    response: Response,
    tag: Optional[str] = Query(None, description="Tag name to filter by"),
    judge: Optional[str] = Query(None, description="Judge name to filter by"),
    participant: Optional[str] = Query(
        None, description="Participant name to filter by"
    ),
    lawyer: Optional[str] = Query(None, description="Lawyer name to filter by"),
    law_firm: Optional[str] = Query(None, description="Law firm name to filter by"),
    title: Optional[str] = Query(None, description="Title to filter by"),
    citation: Optional[str] = Query(None, description="Citation to filter by"),
    verdict: Optional[str] = Query(None, description="Verdict to filter by"),
    court: Optional[str] = Query(None, description="Court name to filter by"),
    start_date: Optional[date] = Query(
        None, description="Start date to filter by in the form YYYY-MM-DD"
    ),
    end_date: Optional[date] = Query(
        None, description="End date to filter by in the form YYYY-MM-DD"
    ),
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    db: Session = Depends(get_db),
):
    """API endpoint to get all columns for a court case with optional search and limit parameters"""
    params = request.query_params
    query_param_list = [
        "tag",
        "judge",
        "participant",
        "lawyer",
        "law_firm",
        "title",
        "citation",
        "verdict",
        "court",
        "start_date",
        "end_date",
        "limit",
    ]
    validate_query_params(params, query_param_list)
    query = db.query(CourtCase).options(
        selectinload(CourtCase.tags),
        selectinload(CourtCase.judges),
        selectinload(CourtCase.participant_assignments).selectinload(
            ParticipantAssignment.participant
        ),
        selectinload(CourtCase.participant_assignments)
        .selectinload(ParticipantAssignment.lawyer)
        .selectinload(Lawyer.law_firm),
    )

    if tag:
        query = query.join(CourtCase.tags).where(Tag.tag_name.ilike(f"%{tag}%"))

    if judge:
        query = query.join(CourtCase.judges).where(Judge.judge_name.ilike(f"%{judge}%"))

    if participant:
        query = (
            query.join(CourtCase.participant_assignments)
            .join(ParticipantAssignment.participant)
            .where(Participant.participant_name.lower() == participant.lower())
        )

    if lawyer:
        query = (
            query.join(CourtCase.participant_assignments)
            .join(ParticipantAssignment.lawyer)
            .where(Lawyer.lawyer_name.ilike(f"%{lawyer}%"))
        )

    if law_firm:
        query = (
            query.join(CourtCase.participant_assignments)
            .join(ParticipantAssignment.lawyer)
            .join(Lawyer.law_firm)
            .where(LawFirm.law_firm_name.ilike(f"%{law_firm}%"))
        )

    if title:
        query = query.where(CourtCase.title.ilike(f"%{title}%"))

    if citation:
        query = query.where(CourtCase.case_number.ilike(f"%{citation}%"))

    if verdict:
        query = query.join(CourtCase.verdict).where(
            Verdict.verdict.ilike(f"%{verdict}%")
        )

    if court:
        query = query.join(CourtCase.court).where(Court.court_name.ilike(f"%{court}%"))

    if start_date:
        query = query.where(CourtCase.court_date >= start_date)

    if end_date:
        query = query.where(CourtCase.court_date <= end_date)

    if limit is not None:
        query = query.limit(limit)

    result = query.all()
    if not result:
        return no_matches(response, "court cases")
    return result


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=80)
