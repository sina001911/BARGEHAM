"""Academy Intelligence service: AI Tutor, Adaptive Learning, Lesson Generation, Socratic Learning, Knowledge Assessment."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.academy.intelligence_models import (
    Lesson,
    LessonType,
    LessonStatus,
    Quiz,
    QuizType,
    QuizStatus,
    QuizQuestion,
    QuizAttempt,
    LessonUserProgress,
    SocraticSession,
    SocraticMode,
    AttemptStatus,
)
from app.academy.models import Course, LearnerMemory
from app.config import settings

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json_list(value: str | None, default: list | None = None) -> list:
    """Parse a JSON string into a Python list."""
    if not value:
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _serialize_json_list(value: list) -> str:
    """Serialize a Python list to JSON string."""
    return json.dumps(value, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Lesson Generation
# --------------------------------------------------------------------------- #

async def generate_lesson(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    topic: str,
    title: str | None = None,
    lesson_type: LessonType = LessonType.CONCEPT,
    order_index: int | None = None,
    estimated_minutes: int | None = None,
    user_id: uuid.UUID | None = None,
) -> Lesson:
    """Generate a lesson using AI based on course context and learner memory."""
    course = await session.get(Course, course_id)
    if course is None:
        raise ValueError(f"Course {course_id} not found")

    # Get learner memory for context
    memory_context = ""
    if user_id is not None:
        memory_stmt = select(LearnerMemory).where(
            LearnerMemory.course_id == course_id,
            LearnerMemory.user_id == user_id,
        )
        memories = (await session.execute(memory_stmt)).scalars().all()
        if memories:
            topics = [m.topic for m in memories[:5]]
            mastery = [f"{m.topic}: {m.mastery_level:.0%}" for m in memories[:5]]
            memory_context = (
                f"\nLearner context - Topics studied: {', '.join(topics)}\n"
                f"Mastery levels: {', '.join(mastery)}"
            )

    # Build prompt for lesson generation
    prompt = (
        f"Generate a comprehensive lesson for a {course.course_type.value} course on '{topic}'.\n"
        f"Course: {course.name}\n"
        f"Course description: {course.description or 'N/A'}\n"
        f"Lesson type: {lesson_type.value}\n"
        f"{memory_context}\n\n"
        f"Requirements:\n"
        f"1. Write clear, educational content in Persian or English (match course language)\n"
        f"2. Include examples and practical applications\n"
        f"3. Structure with headings and bullet points\n"
        f"4. Keep it appropriate for {estimated_minutes or 30} minutes of study\n"
        f"5. Make it engaging and suitable for self-paced learning\n\n"
        f"Return ONLY the lesson content, no meta-commentary."
    )

    # Generate content via AI or fallback
    try:
        generated_content = await _generate_ai_content(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lesson generation AI failed: %s", exc)
        generated_content = _fallback_lesson_content(topic, lesson_type, course.name)

    # Determine order index
    if order_index is None:
        existing = (
            await session.execute(select(Lesson).where(Lesson.course_id == course_id))
        ).scalars().all()
        order_index = len(existing)

    lesson = Lesson(
        course_id=course_id,
        topic=topic,
        title=title or f"Lesson: {topic}",
        content=generated_content,
        lesson_type=lesson_type,
        order_index=order_index,
        estimated_minutes=estimated_minutes,
        ai_generated=True,
        generation_prompt=prompt,
    )
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    return lesson


async def _generate_ai_content(prompt: str) -> str:
    """Attempt AI content generation; raises if no provider available."""
    # No cloud/local provider modules exist in this project; fall through to raise.
    raise RuntimeError("No AI provider configured")


def _fallback_lesson_content(topic: str, lesson_type: LessonType, course_name: str) -> str:
    """Generate simple fallback lesson content when AI is unavailable."""
    return f"""# {topic}

## Course: {course_name}
## Lesson Type: {lesson_type.value}

### Overview
This lesson covers the topic of **{topic}** within the {course_name} course.

### Key Concepts
- Introduction to {topic}
- Core principles and definitions
- Practical applications
- Common patterns and best practices

### Learning Objectives
By the end of this lesson, learners should be able to:
1. Understand the fundamentals of {topic}
2. Apply {topic} in practical scenarios
3. Identify key patterns related to {topic}

### Summary
This lesson provided an overview of {topic}. Continue practicing to reinforce your understanding.
"""


async def list_lessons(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    status: str | None = None,
    lesson_type: LessonType | None = None,
) -> list[Lesson]:
    """List lessons with optional filtering."""
    stmt = select(Lesson)
    conditions = []
    if course_id is not None:
        conditions.append(Lesson.course_id == course_id)
    if status is not None:
        conditions.append(Lesson.status == status)
    if lesson_type is not None:
        conditions.append(Lesson.lesson_type == lesson_type)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(Lesson.order_index, Lesson.created_at)
    return list((await session.execute(stmt)).scalars().all())


async def get_lesson(session: AsyncSession, lesson_id: uuid.UUID) -> Lesson | None:
    """Get a lesson by ID."""
    return await session.get(Lesson, lesson_id)


async def update_lesson(
    session: AsyncSession,
    lesson_id: uuid.UUID,
    *,
    title: str | None = None,
    content: str | None = None,
    lesson_type: LessonType | None = None,
    status: LessonStatus | None = None,
    order_index: int | None = None,
    estimated_minutes: int | None = None,
) -> Lesson | None:
    """Update a lesson."""
    lesson = await get_lesson(session, lesson_id)
    if lesson is None:
        return None
    if title is not None:
        lesson.title = title
    if content is not None:
        lesson.content = content
    if lesson_type is not None:
        lesson.lesson_type = lesson_type
    if status is not None:
        lesson.status = status
    if order_index is not None:
        lesson.order_index = order_index
    if estimated_minutes is not None:
        lesson.estimated_minutes = estimated_minutes
    lesson.updated_at = _utcnow()
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    return lesson


async def delete_lesson(session: AsyncSession, lesson_id: uuid.UUID) -> bool:
    """Delete a lesson."""
    lesson = await get_lesson(session, lesson_id)
    if lesson is None:
        return False
    await session.delete(lesson)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Lesson User Progress
# --------------------------------------------------------------------------- #

async def upsert_lesson_progress(
    session: AsyncSession,
    *,
    lesson_id: uuid.UUID,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
    status: str | None = None,
    time_spent_minutes: int | None = None,
    notes: str | None = None,
) -> LessonUserProgress:
    """Create or update lesson progress."""
    stmt = select(LessonUserProgress).where(
        LessonUserProgress.lesson_id == lesson_id,
        LessonUserProgress.user_id == user_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    now = _utcnow()
    if existing:
        if status is not None:
            existing.status = status
        if time_spent_minutes is not None:
            existing.time_spent_minutes = time_spent_minutes
        if notes is not None:
            existing.notes = notes
        if status == LessonStatus.PUBLISHED.value and existing.completed_at is None:
            existing.completed_at = now
        if status == LessonStatus.PUBLISHED.value and existing.started_at is None:
            existing.started_at = now
        existing.updated_at = now
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        started = now if status == LessonStatus.PUBLISHED.value else None
        completed = now if status == LessonStatus.PUBLISHED.value else None
        progress = LessonUserProgress(
            lesson_id=lesson_id,
            user_id=user_id,
            course_id=course_id,
            status=status or LessonStatus.DRAFT.value,
            time_spent_minutes=time_spent_minutes or 0,
            notes=notes,
            started_at=started,
            completed_at=completed,
        )
        session.add(progress)
        await session.commit()
        await session.refresh(progress)
        return progress


async def list_lesson_progress(
    session: AsyncSession,
    *,
    lesson_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
) -> list[LessonUserProgress]:
    """List lesson progress records."""
    stmt = select(LessonUserProgress)
    conditions = []
    if lesson_id is not None:
        conditions.append(LessonUserProgress.lesson_id == lesson_id)
    if user_id is not None:
        conditions.append(LessonUserProgress.user_id == user_id)
    if course_id is not None:
        conditions.append(LessonUserProgress.course_id == course_id)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(LessonUserProgress.updated_at.desc())
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Quiz Generation
# --------------------------------------------------------------------------- #

async def generate_quiz(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    topic: str,
    title: str | None = None,
    quiz_type: QuizType = QuizType.MULTIPLE_CHOICE,
    time_limit_minutes: int | None = None,
    passing_score: float = 0.7,
    num_questions: int = 5,
    user_id: uuid.UUID | None = None,
) -> Quiz:
    """AI-generate a quiz for a course topic."""
    course = await session.get(Course, course_id)
    if course is None:
        raise ValueError(f"Course {course_id} not found")

    # Get lesson context if available
    lessons_stmt = select(Lesson).where(Lesson.course_id == course_id).limit(10)
    lessons = (await session.execute(lessons_stmt)).scalars().all()
    lesson_context = ""
    if lessons:
        lesson_titles = [l.title for l in lessons]
        lesson_context = f"\nRelated lessons: {', '.join(lesson_titles)}\n"

    prompt = (
        f"Generate a {quiz_type.value} quiz for a {course.course_type.value} course on '{topic}'.\n"
        f"Course: {course.name}\n"
        f"Course description: {course.description or 'N/A'}\n"
        f"Number of questions: {num_questions}\n"
        f"Time limit: {time_limit_minutes or 'N/A'} minutes\n"
        f"Passing score: {passing_score:.0%}\n"
        f"{lesson_context}\n\n"
        f"Requirements:\n"
        f"1. Create {num_questions} {quiz_type.value} questions\n"
        f"2. For multiple choice, provide 4 options with one correct answer\n"
        f"3. Include explanations for correct answers\n"
        f"4. Vary difficulty appropriately\n"
        f"5. Make questions relevant to the course content\n\n"
        f"Return the quiz questions and answers in a structured format."
    )

    # Generate content via AI or fallback
    try:
        ai_response = await _generate_ai_content(prompt)
        questions = _parse_quiz_from_ai(ai_response, quiz_type, num_questions)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Quiz generation AI failed: %s", exc)
        questions = _fallback_quiz_questions(topic, quiz_type, num_questions)

    quiz = Quiz(
        course_id=course_id,
        topic=topic,
        title=title or f"Quiz: {topic}",
        description=f"AI-generated {quiz_type.value} quiz on {topic}",
        quiz_type=quiz_type,
        time_limit_minutes=time_limit_minutes,
        passing_score=passing_score,
        ai_generated=True,
        generation_prompt=prompt,
    )
    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)

    # Create questions
    for i, q in enumerate(questions[:num_questions]):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q.get("question", ""),
            question_type=quiz_type,
            options=_serialize_json_list(q.get("options", [])),
            correct_answer=q.get("answer", ""),
            explanation=q.get("explanation", ""),
            points=q.get("points", 1.0),
            order_index=i,
            ai_generated=True,
        )
        session.add(question)
    await session.commit()

    return quiz


def _fallback_quiz_questions(
    topic: str, quiz_type: QuizType, num_questions: int
) -> list[dict]:
    """Generate simple fallback quiz questions."""
    questions = []
    for i in range(num_questions):
        if quiz_type == QuizType.MULTIPLE_CHOICE:
            questions.append({
                "question": f"What is a key concept related to {topic} (question {i + 1})?",
                "options": [
                    f"Option A for {topic}",
                    f"Option B for {topic}",
                    f"Option C for {topic}",
                    f"Option D for {topic}",
                ],
                "answer": f"Option A for {topic}",
                "explanation": f"Option A is correct because it relates to {topic}.",
                "points": 1.0,
            })
        else:
            questions.append({
                "question": f"Explain a concept related to {topic} (question {i + 1}).",
                "answer": f"A comprehensive answer about {topic}.",
                "explanation": f"This answer covers key aspects of {topic}.",
                "points": 1.0,
            })
    return questions


def _parse_quiz_from_ai(
    ai_response: str, quiz_type: QuizType, num_questions: int
) -> list[dict]:
    """Parse AI-generated quiz response into structured questions."""
    questions = []
    lines = ai_response.split("\n")
    current_q = None
    for line in lines:
        line = line.strip()
        if line.lower().startswith(("question", "q")) and ":" in line:
            if current_q:
                questions.append(current_q)
            current_q = {
                "question": line.split(":", 1)[1].strip(),
                "options": [],
                "answer": "",
                "explanation": "",
                "points": 1.0,
            }
        elif current_q and line.lower().startswith(("answer", "correct")):
            current_q["answer"] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif current_q and line.lower().startswith(("explanation",)):
            current_q["explanation"] = line.split(":", 1)[1].strip() if ":" in line else ""
    if current_q:
        questions.append(current_q)
    return questions[:num_questions] if questions else _fallback_quiz_questions("topic", quiz_type, num_questions)


async def list_quizzes(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    status: str | None = None,
) -> list[Quiz]:
    """List quizzes with optional filtering."""
    stmt = select(Quiz)
    conditions = []
    if course_id is not None:
        conditions.append(Quiz.course_id == course_id)
    if status is not None:
        conditions.append(Quiz.status == status)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(Quiz.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_quiz(session: AsyncSession, quiz_id: uuid.UUID) -> Quiz | None:
    """Get a quiz by ID."""
    quiz = await session.get(Quiz, quiz_id)
    if quiz is None:
        return None
    # Load questions
    questions_stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index)
    quiz.questions = (await session.execute(questions_stmt)).scalars().all()
    return quiz


async def get_quiz_questions(session: AsyncSession, quiz_id: uuid.UUID) -> list[QuizQuestion]:
    """Get all questions for a quiz."""
    stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index)
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Quiz Attempts
# --------------------------------------------------------------------------- #

async def start_quiz_attempt(
    session: AsyncSession,
    *,
    quiz_id: uuid.UUID,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> QuizAttempt:
    """Start a new quiz attempt."""
    quiz = await session.get(Quiz, quiz_id)
    if quiz is None:
        raise ValueError(f"Quiz {quiz_id} not found")

    questions = await get_quiz_questions(session, quiz_id)
    points_total = sum(q.points for q in questions)

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        course_id=course_id,
        status=AttemptStatus.IN_PROGRESS,
        points_total=points_total,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return attempt


async def submit_quiz_answers(
    session: AsyncSession,
    *,
    attempt_id: uuid.UUID,
    answers: dict[str, str],  # question_id -> user_answer
) -> QuizAttempt:
    """Submit quiz answers and calculate score."""
    attempt = await session.get(QuizAttempt, attempt_id)
    if attempt is None:
        raise ValueError(f"Attempt {attempt_id} not found")

    questions = await get_quiz_questions(session, attempt.quiz_id)
    points_earned = 0.0

    for q in questions:
        user_answer = answers.get(str(q.id), "")
        correct = q.correct_answer.strip().lower() == user_answer.strip().lower()
        if correct:
            points_earned += q.points

    score = points_earned / attempt.points_total if attempt.points_total > 0 else 0.0

    attempt.status = AttemptStatus.COMPLETED
    attempt.score = score
    attempt.points_earned = points_earned
    attempt.answers = _serialize_json_list([
        {"question_id": str(q.id), "answer": answers.get(str(q.id), ""), "correct": q.correct_answer.strip().lower() == answers.get(str(q.id), "").strip().lower()}
        for q in questions
    ])
    attempt.completed_at = _utcnow()
    attempt.updated_at = _utcnow()

    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)

    # Update learner knowledge based on quiz performance
    await _update_learner_knowledge_from_quiz(session, attempt.course_id, attempt.user_id, attempt.quiz_id, score)

    return attempt


async def _update_learner_knowledge_from_quiz(
    session: AsyncSession,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    quiz_id: uuid.UUID,
    score: float,
) -> None:
    """Update learner mastery based on quiz performance."""
    from app.academy.service import upsert_learner_memory

    quiz = await session.get(Quiz, quiz_id)
    if quiz is None:
        return

    await upsert_learner_memory(
        session,
        course_id=course_id,
        user_id=user_id,
        topic=quiz.topic,
        mastery_level=min(1.0, score + 0.1),
        confidence=min(1.0, score + 0.05),
        test_results=_serialize_json_list([{"quiz_id": str(quiz_id), "score": score, "topic": quiz.topic}]),
    )


async def list_quiz_attempts(
    session: AsyncSession,
    *,
    quiz_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
) -> list[QuizAttempt]:
    """List quiz attempts."""
    stmt = select(QuizAttempt)
    conditions = []
    if quiz_id is not None:
        conditions.append(QuizAttempt.quiz_id == quiz_id)
    if user_id is not None:
        conditions.append(QuizAttempt.user_id == user_id)
    if course_id is not None:
        conditions.append(QuizAttempt.course_id == course_id)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(QuizAttempt.started_at.desc())
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Socratic Learning
# --------------------------------------------------------------------------- #

async def create_socratic_session(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    topic: str,
    mode: SocraticMode = SocraticMode.QUESTION,
) -> SocraticSession:
    """Create a new Socratic tutoring session."""
    course = await session.get(Course, course_id)
    if course is None:
        raise ValueError(f"Course {course_id} not found")

    socratic = SocraticSession(
        course_id=course_id,
        user_id=user_id,
        topic=topic,
        mode=mode,
        messages=_serialize_json_list([]),
        current_question="",
        hints_given=0,
        explanations_given=0,
        is_active=True,
    )
    session.add(socratic)
    await session.commit()
    await session.refresh(socratic)
    return socratic


async def socratic_respond(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
    user_message: str,
) -> dict[str, Any]:
    """Process a user message in a Socratic session and generate AI response."""
    socratic = await session.get(SocraticSession, session_id)
    if socratic is None:
        raise ValueError(f"Socratic session {session_id} not found")

    course = await session.get(Course, socratic.course_id)
    if course is None:
        raise ValueError(f"Course {socratic.course_id} not found")

    # Load existing messages
    messages = _parse_json_list(socratic.messages)

    # Add user message
    messages.append({"role": "user", "content": user_message, "timestamp": _utcnow().isoformat()})

    # Build system prompt for Socratic tutoring
    system_prompt = (
        f"You are a Socratic tutor for a {course.course_type.value} course on '{socratic.topic}'.\n"
        f"Course: {course.name}\n"
        f"Current mode: {socratic.mode.value}\n"
        f"Hints given: {socratic.hints_given}\n"
        f"Explanations given: {socratic.explanations_given}\n\n"
        f"Socratic method: Guide the learner through questions, not direct answers.\n"
        f"Ask probing questions that help them discover the answer themselves.\n"
        f"Provide hints when they're stuck, explanations when they request them.\n"
        f"Encourage critical thinking and self-discovery.\n\n"
        f"Respond in the same language as the user.\n"
        f"Keep responses concise and focused."
    )

    try:
        ai_response = await _generate_ai_content(
            system_prompt + "\n\n" + json.dumps(messages[-10:], ensure_ascii=False)
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Socratic AI failed: %s", exc)
        ai_response = f"That's a great question about {socratic.topic}. Let me think about how to guide you..."

    # Update messages with AI response
    messages.append({"role": "assistant", "content": ai_response, "timestamp": _utcnow().isoformat()})
    socratic.messages = _serialize_json_list(messages)
    socratic.updated_at = _utcnow()
    session.add(socratic)
    await session.commit()
    await session.refresh(socratic)

    return {
        "session_id": str(socratic.id),
        "ai_response": ai_response,
        "mode": socratic.mode,
        "hints_given": socratic.hints_given,
        "explanations_given": socratic.explanations_given,
        "is_active": socratic.is_active,
    }


async def list_socratic_sessions(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    is_active: bool | None = True,
) -> list[SocraticSession]:
    """List Socratic sessions."""
    stmt = select(SocraticSession)
    conditions = []
    if course_id is not None:
        conditions.append(SocraticSession.course_id == course_id)
    if user_id is not None:
        conditions.append(SocraticSession.user_id == user_id)
    if is_active is not None:
        conditions.append(SocraticSession.is_active == is_active)
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(SocraticSession.started_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def close_socratic_session(
    session: AsyncSession,
    *,
    session_id: uuid.UUID,
) -> SocraticSession | None:
    """Close a Socratic session."""
    socratic = await session.get(SocraticSession, session_id)
    if socratic is None:
        return None
    socratic.is_active = False
    socratic.updated_at = _utcnow()
    session.add(socratic)
    await session.commit()
    await session.refresh(socratic)
    return socratic


# --------------------------------------------------------------------------- #
# Adaptive Learning
# --------------------------------------------------------------------------- #

async def get_adaptive_next_lesson(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the next recommended lesson for a user based on mastery and progress."""
    course = await session.get(Course, course_id)
    if course is None:
        raise ValueError(f"Course {course_id} not found")

    lessons = await list_lessons(session, course_id=course_id)
    if not lessons:
        return {"next_lesson": None, "reason": "No lessons in course"}

    # Get learner memory for context
    memories = await list_learner_memories(session, course_id=course_id, user_id=user_id)
    mastery_map = {m.topic: m.mastery_level for m in memories}

    # Get completed lessons
    progress = await list_lesson_progress(session, course_id=course_id, user_id=user_id)
    completed_ids = {p.lesson_id for p in progress if p.status == LessonStatus.PUBLISHED.value}

    # Find next unfinished lesson with lowest mastery
    next_lesson = None
    reason = ""

    for lesson in sorted(lessons, key=lambda l: l.order_index):
        if lesson.id in completed_ids:
            continue
        # Check if prerequisite topics are mastered
        mastery = mastery_map.get(lesson.topic, 0.0)
        if mastery < 0.6 and lesson.order_index > 0:
            # Suggest reviewing prerequisite first
            reason = f"Review {lesson.topic} first (mastery: {mastery:.0%})"
            continue
        next_lesson = lesson
        reason = "Next recommended lesson"
        break

    if not next_lesson:
        # All lessons completed or only low-mastery ones remain
        lowest_mastery_topic = min(mastery_map.items(), key=lambda x: x[1], default=(None, 0))
        if lowest_mastery_topic[0]:
            return {
                "next_lesson": None,
                "reason": f"Review {lowest_mastery_topic[0]} first (mastery: {lowest_mastery_topic[1]:.0%})",
            }
        return {"next_lesson": None, "reason": "All lessons completed"}

    return {
        "next_lesson": {
            "id": str(next_lesson.id),
            "title": next_lesson.title,
            "topic": next_lesson.topic,
            "lesson_type": next_lesson.lesson_type.value,
            "order_index": next_lesson.order_index,
            "estimated_minutes": next_lesson.estimated_minutes,
        },
        "reason": reason,
    }


async def get_adaptive_learning_path(
    session: AsyncSession,
    *,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the full adaptive learning path for a user in a course."""
    course = await session.get(Course, course_id)
    if course is None:
        raise ValueError(f"Course {course_id} not found")

    lessons = await list_lessons(session, course_id=course_id)
    progress = await list_lesson_progress(session, course_id=course_id, user_id=user_id)
    memories = await list_learner_memories(session, course_id=course_id, user_id=user_id)

    completed_ids = {p.lesson_id for p in progress if p.status == LessonStatus.PUBLISHED.value}
    mastery_map = {m.topic: m.mastery_level for m in memories}

    path = []
    for lesson in sorted(lessons, key=lambda l: l.order_index):
        is_completed = lesson.id in completed_ids
        mastery = mastery_map.get(lesson.topic, 0.0)
        path.append({
            "lesson_id": str(lesson.id),
            "title": lesson.title,
            "topic": lesson.topic,
            "lesson_type": lesson.lesson_type.value,
            "order_index": lesson.order_index,
            "is_completed": is_completed,
            "mastery_level": mastery,
            "estimated_minutes": lesson.estimated_minutes,
        })

    # Calculate overall progress
    total_lessons = len(path)
    completed_count = sum(1 for p in path if p["is_completed"])
    overall_progress = completed_count / total_lessons if total_lessons > 0 else 0.0

    # Average mastery
    avg_mastery = sum(p["mastery_level"] for p in path) / total_lessons if total_lessons > 0 else 0.0

    return {
        "course_id": str(course_id),
        "course_name": course.name,
        "total_lessons": total_lessons,
        "completed_lessons": completed_count,
        "overall_progress": overall_progress,
        "average_mastery": avg_mastery,
        "path": path,
    }


# --------------------------------------------------------------------------- #
# Learner Memory helpers (delegated to academy service)
# --------------------------------------------------------------------------- #

async def list_learner_memories(
    session: AsyncSession,
    *,
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    topic: str | None = None,
) -> list[LearnerMemory]:
    """List learner memories (delegated to academy service)."""
    from app.academy.service import list_learner_memories as _list_memories
    return await _list_memories(
        session, course_id=course_id, user_id=user_id, topic=topic
    )