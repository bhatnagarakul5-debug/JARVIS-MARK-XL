"""
actions/exam_companion.py — Academic Exam Companion, Tutor & Document Intelligence for JARVIS Mark 58
Provides high-level academic intelligence:
- Document reading, analysis, and syllabus breakdown (PDF, DOCX, PPTX, Images/OCR, Test papers).
- Multi-mode concept explanations: Feynman technique, in-depth mathematical rigor, or rapid cram.
- Interactive Socratic Drill, mock tests, and flashcards with instant evaluation.
- Step-by-step problem solver for derivations, numericals, and past paper questions.
- Automated export of exam revision sheets and slide decks to Word, PDF, or PowerPoint.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from core.ai_client import generate_text_with_retry, get_api_key as _get_api_key

def _extract_document_text(file_path: str) -> tuple[str, str]:
    """Extracts text from PDF, DOCX, PPTX, TXT, or Image (via Gemini Vision)."""
    p = Path(file_path).expanduser()
    if not p.exists():
        # Check desktop/downloads shortcuts
        cand_desk = Path.home() / "OneDrive" / "Desktop" / file_path
        if cand_desk.exists(): p = cand_desk
        cand_down = Path.home() / "OneDrive" / "Downloads" / file_path
        if cand_down.exists(): p = cand_down

    if not p.exists():
        return "", f"File not found: '{file_path}'"

    ext = p.suffix.lower()
    text = ""

    # 1. PDF
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(p))
            for idx, page in enumerate(reader.pages[:40]): # First 40 pages
                t = page.extract_text()
                if t: text += f"\n--- Page {idx+1} ---\n" + t
            return text.strip(), ""
        except Exception as e:
            return "", f"PDF extraction error: {e}"

    # 2. Word (.docx)
    elif ext in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(p))
            for para in doc.paragraphs:
                if para.text.strip(): text += para.text + "\n"
            return text.strip(), ""
        except Exception as e:
            return "", f"DOCX extraction error: {e}"

    # 3. PowerPoint (.pptx)
    elif ext in (".pptx", ".ppt"):
        try:
            from pptx import Presentation
            prs = Presentation(str(p))
            for idx, slide in enumerate(prs.slides):
                text += f"\n--- Slide {idx+1} ---\n"
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            if paragraph.text.strip():
                                text += paragraph.text + "\n"
            return text.strip(), ""
        except Exception as e:
            return "", f"PPTX extraction error: {e}"

    # 4. Text / Markdown / Code
    elif ext in (".txt", ".md", ".csv", ".json", ".py"):
        try:
            return p.read_text(encoding="utf-8", errors="ignore"), ""
        except Exception as e:
            return "", f"Text file read error: {e}"

    # 5. Image (Diagram, Whiteboard, Handwritten test) via Gemini Multimodal Vision
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        api_key = _get_api_key()
        if not api_key:
            return "", "Gemini API key missing for image document processing."
        try:
            client = genai.Client(api_key=api_key)
            img_bytes = p.read_bytes()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type=mime),
                    "Carefully transcribe all text, formulas, diagrams, questions, and notes from this academic document/image."
                ]
            )
            return res.text.strip() if res and res.text else "", ""
        except Exception as e:
            return "", f"Image vision OCR error: {e}"

    return "", f"Unsupported file extension: {ext}"


def exam_companion(parameters: dict, player=None) -> str:
    """
    JARVIS Academic Exam Companion & Document Intelligence Engine.
    parameters:
      action: 'explain' | 'analyze_document' | 'quiz_me' | 'solve_question' | 'study_plan' | 'create_cheat_sheet'
      topic: Subject or topic name
      file_path: Optional path to uploaded document (PDF, PPTX, DOCX, image)
      mode: 'feynman' | 'deep' | 'cram' | 'mcq' | 'step_by_step'
      export_to: 'none' | 'docx' | 'pdf' | 'pptx'
    """
    params = parameters or {}
    action = (params.get("action") or "explain").lower().strip()
    topic = (params.get("topic") or "").strip()
    file_path = params.get("file_path") or ""
    mode = (params.get("mode") or "feynman").lower().strip()
    export_to = (params.get("export_to") or "none").lower().strip()

    api_key = _get_api_key()
    if not api_key:
        return "Sir, Gemini API Key is required for the Exam Companion engine."

    doc_text = ""
    doc_note = ""
    if file_path:
        if player and hasattr(player, "write_log"):
            player.write_log(f"EXAM ENGINE: Extracting academic document '{Path(file_path).name}'...")
        doc_text, err = _extract_document_text(file_path)
        if err:
            doc_note = f"\n[Document Notice: {err}]"

    client = genai.Client(api_key=api_key)

    # 1. EXPLAIN TOPIC / CONCEPT
    if action in ("explain", "explain_topic", "tutor", "teach"):
        style_prompt = {
            "feynman": "Explain using the Feynman Technique: crystal-clear, relatable real-world analogies, zero unnecessary jargon, intuitive mental models, followed by high-yield key takeaways.",
            "deep": "Provide deep academic and mathematical rigor: state formal definitions, core equations, derivations, assumptions, boundary conditions, and edge cases.",
            "cram": "Provide an ultra-condensed Exam Cram breakdown: 5-bullet summary, essential formulas, high-probability exam questions, and common mistakes students lose marks on."
        }.get(mode, "Explain clearly with structure, intuitive examples, and key takeaways.")

        prompt = (
            f"You are J.A.R.V.I.S., Akul's brilliant academic mentor and exam companion.\n"
            f"Topic to explain: {topic or 'the uploaded document'}\n"
            f"Style: {style_prompt}\n"
        )
        if doc_text:
            prompt += f"\nContext from uploaded lecture/textbook ({len(doc_text)} chars):\n```\n{doc_text[:12000]}\n```\n"

        prompt += "\nFormat with markdown headers, bold terms, and bullet points. Be concise, engaging, and direct."

        output = generate_text_with_retry(prompt, client=client)

        # Handle optional export
        if export_to in ("docx", "pdf", "pptx"):
            from actions.file_generator import universal_file_creator
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic or 'Exam_Revision')[:25]
            f_res = universal_file_creator({
                "file_type": export_to,
                "filename": f"{clean_name}_Study_Notes",
                "title": f"Study Guide: {topic.title() if topic else 'Academic Revision'}",
                "content": output,
                "open_after": True
            }, player=player)
            output += f"\n\n📁 **Exported**: {f_res}"

        return output + doc_note

    # 2. ANALYZE DOCUMENT / SYLLABUS
    elif action in ("analyze_document", "analyze", "breakdown", "summarize_doc"):
        if not doc_text:
            return f"Please provide an uploaded document (PDF, Word, PPTX, or Image notes) to analyze, sir.{doc_note}"

        prompt = (
            "You are J.A.R.V.I.S., Akul's academic exam wingman.\n"
            "Analyze the following college lecture/textbook document:\n"
            "1. Executive Summary of the material\n"
            "2. Core Concepts, Definitions & Formulas (with explanations)\n"
            "3. Top 5 High-Probability Exam Questions based on this content\n"
            "4. Common Pitfalls & Traps to avoid in exams\n\n"
            f"Document Content:\n```\n{doc_text[:15000]}\n```"
        )
        output = generate_text_with_retry(prompt, client=client)

        if export_to in ("docx", "pdf", "pptx"):
            from actions.file_generator import universal_file_creator
            f_name = Path(file_path).stem if file_path else "Document_Analysis"
            f_res = universal_file_creator({
                "file_type": export_to,
                "filename": f"{f_name}_Exam_Analysis",
                "title": f"Exam Breakdown: {f_name.replace('_', ' ').title()}",
                "content": output,
                "open_after": True
            }, player=player)
            output += f"\n\n📁 **Exported**: {f_res}"

        return output

    # 3. QUIZ ME / FLASHCARDS
    elif action in ("quiz_me", "quiz", "mock_test", "flashcards"):
        prompt = (
            f"You are J.A.R.V.I.S., running a high-yield exam drill session for Akul on: {topic or 'the uploaded material'}.\n"
            "Generate 5 sharp, realistic college exam questions (3 Multiple Choice with options A/B/C/D, 2 Short Analytical).\n"
            "Include the Answer Key with concise explanations at the end under a '--- ANSWER KEY ---' divider so Akul can test himself first."
        )
        if doc_text:
            prompt += f"\nSource Material:\n```\n{doc_text[:12000]}\n```"

        return generate_text_with_retry(prompt, client=client)

    # 4. SOLVE QUESTION / DERIVATION
    elif action in ("solve_question", "solve", "math", "derivation"):
        prompt = (
            f"You are J.A.R.V.I.S., assisting Akul with solving an exam question.\n"
            f"Problem Statement: {topic}\n"
        )
        if doc_text:
            prompt += f"\nContext/Reference Material:\n```\n{doc_text[:10000]}\n```"
        prompt += (
            "\nProvide:\n"
            "1. Given variables and what needs to be solved\n"
            "2. Relevant governing formulas and principles\n"
            "3. Step-by-step rigorous solution and intermediate calculations\n"
            "4. Final Boxed Answer with appropriate units\n"
            "5. Sanity check: Why this answer makes intuitive sense."
        )
        return generate_text_with_retry(prompt, client=client)

    # 5. STUDY PLAN / REVISION SCHEDULE
    elif action in ("study_plan", "revision_schedule", "plan"):
        days = params.get("days", 7)
        prompt = (
            f"You are J.A.R.V.I.S., creating an optimized, realistic {days}-day exam revision schedule for Akul.\n"
            f"Subject/Scope: {topic or 'Upcoming College Finals'}\n"
            "Divide the syllabus logically across each day with: Morning Focus, Afternoon Practice/Numericals, and Evening Active Recall. "
            "Include dedicated buffer hours for mock test simulation."
        )
        output = generate_text_with_retry(prompt, client=client)

        if export_to in ("docx", "xlsx", "pdf"):
            from actions.file_generator import universal_file_creator
            f_res = universal_file_creator({
                "file_type": export_to,
                "filename": "Exam_Revision_Schedule",
                "title": f"{days}-Day Revision Roadmap",
                "content": output,
                "open_after": True
            }, player=player)
            output += f"\n\n📁 **Schedule Exported**: {f_res}"

        return output

    # 6. CRAM SHEET EXPORT
    elif action in ("create_cheat_sheet", "cram_sheet", "formula_sheet"):
        prompt = (
            f"You are J.A.R.V.I.S. Create a master 1-page high-yield Exam Formula & Cheat Sheet for: {topic or 'College Course'}.\n"
            "Organize strictly into:\n"
            "1. Must-Know Definitions\n"
            "2. Core Formulas & Variables\n"
            "3. Key Theorems / Decision Rules\n"
            "4. The 3 Most Common Exam Mistakes"
        )
        if doc_text:
            prompt += f"\nSource Material:\n```\n{doc_text[:14000]}\n```"

        output = generate_text_with_retry(prompt, client=client)

        from actions.file_generator import universal_file_creator
        clean_t = re.sub(r'[^a-zA-Z0-9_-]', '_', topic or 'Subject')[:20]
        fmt = export_to if export_to in ("pdf", "docx", "pptx") else "pdf"
        f_res = universal_file_creator({
            "file_type": fmt,
            "filename": f"{clean_t}_Master_Cheat_Sheet",
            "title": f"Master Cheat Sheet: {topic.title() if topic else 'Course Revision'}",
            "content": output,
            "open_after": True
        }, player=player)

        return f"{output}\n\n📁 **Cheat Sheet Created & Opened**: {f_res}"

    return f"Unknown exam_companion action: '{action}'. Available: explain, analyze_document, quiz_me, solve_question, study_plan, create_cheat_sheet"
