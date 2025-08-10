import json
import faiss
import numpy as np
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# --- Load employee data ---
try:
    with open("employees.json", "r") as f:
        raw_data = json.load(f)
        employees_data = raw_data["employees"]
except (FileNotFoundError, KeyError) as e:
    print(f"Error loading employee data: {e}")
    employees_data = []

# --- Prepare embeddings ---
model = SentenceTransformer('all-MiniLM-L6-v2')
employee_docs = [
    f"Name: {emp['name']}. Skills: {', '.join(emp['skills'])}. "
    f"Experience: {emp['experience_years']} years. Projects: {', '.join(emp['projects'])}."
    for emp in employees_data
]
employee_embeddings = model.encode(employee_docs)
d = employee_embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(np.array(employee_embeddings).astype('float32'))

# --- FastAPI setup ---
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://chatbot-assignment-beige.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the HR Chatbot API!"}

@app.post("/chat")
@app.post("/chat")
def chat_with_rag(request: ChatRequest):
    try:
        query_lower = request.query.lower().strip()

        # --- Extract all skills ---
        all_skills = set(skill.lower() for emp in employees_data for skill in emp['skills'])

        # Step 1: Exact skill match
        matched_skill = next(
            (skill for skill in all_skills if re.fullmatch(re.escape(query_lower), skill)),
            None
        )

        retrieved_employees = []

        if matched_skill:
            retrieved_employees = [
                emp for emp in employees_data
                if any(re.fullmatch(re.escape(matched_skill), s.lower()) for s in emp['skills'])
            ]

        # Step 2: FAISS fallback
        if not retrieved_employees:
            query_embedding = model.encode([request.query])
            distances, indices = index.search(np.array(query_embedding).astype('float32'), k=3)
            retrieved_employees = [
                employees_data[i] for i in indices[0] if i < len(employees_data)
            ]

        # Step 3: No results
        if not retrieved_employees:
            return {"response": {
                "intro": "",
                "candidates": [],
                "closing": "I couldn't find any employees matching that query."
            }}

        # --- Expertise & Domain detection (ONLY from query) ---
        expertise_keywords = [
            "machine learning", "ml", "deep learning", "ai", "artificial intelligence",
            "frontend", "backend", "fullstack", "devops", "cloud", "data science", "nlp",
            "computer vision", "cybersecurity", "mobile development", "blockchain"
        ]
        expertise_found = next((kw for kw in expertise_keywords if kw in query_lower), None)

        domain_keywords = [
            "healthcare", "finance", "banking", "education", "ecommerce", "cloud",
            "iot", "logistics", "retail", "manufacturing", "gaming"
        ]
        domain_found = next((kw for kw in domain_keywords if kw in query_lower), None)

        # --- Intro line ---
        num_candidates = len(retrieved_employees)
        candidate_word = "candidate" if num_candidates == 1 else "candidates"

        if expertise_found and domain_found:
            intro_line = f"Based on your requirements for {expertise_found.upper()} expertise in {domain_found}, I found {num_candidates} excellent {candidate_word}:"
        elif expertise_found:
            intro_line = f"Based on your requirements for {expertise_found.upper()} expertise, I found {num_candidates} excellent {candidate_word}:"
        elif domain_found:
            intro_line = f"Based on your requirements in {domain_found}, I found {num_candidates} excellent {candidate_word}:"
        else:
            intro_line = f"Based on your requirements, I found {num_candidates} excellent {candidate_word}:"

        # --- Candidate data ---
        candidate_blocks = []
        for idx, emp in enumerate(retrieved_employees):
            pronoun = "He" if emp.get('gender') == 'male' else "She"
            intro_phrase = (
                f"**{emp['name']}** would be perfect for this role." if idx == 0
                else f"**{emp['name']}** is another strong candidate."
            )

            if 'bio' in emp:
                detail_text = emp['bio']
            else:
                detail_text = (
                    f"{intro_phrase} {pronoun} has {emp['experience_years']} years of experience and "
                    f"skills in {', '.join(emp['skills'])}. "
                    f"{pronoun} has worked on {', '.join(emp['projects'])}. "
                    f"{pronoun} is currently {emp['availability']}."
                )

            candidate_blocks.append(detail_text)

        # --- Closing ---
        if num_candidates == 1:
            closing_line = (
                f"This candidate has the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )
        elif num_candidates == 2:
            closing_line = (
                f"Both have the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )
        else:
            closing_line = (
                f"All of them have the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )

        return {
            "response": {
                "intro": intro_line,
                "candidates": candidate_blocks,
                "closing": closing_line
            }
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/employees/search")
def search_employees(query: str):
    query_lower = query.lower()
    found_employees = [
        emp for emp in employees_data
        if (query_lower in emp['name'].lower() or
            any(query_lower in skill.lower() for skill in emp['skills']) or
            any(query_lower in proj.lower() for proj in emp['projects']))
    ]
    return {"results": found_employees}
