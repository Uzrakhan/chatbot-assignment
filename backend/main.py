import json
import faiss
import numpy as np
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


# --- 1. CONFIGURATION AND IMPORTS ---
# No LLM client configuration is needed for the "Simple" method.

# --- 2. DATA LAYER & RAG RETRIEVAL SETUP ---
# This block runs once when the server starts, setting up the searchable index

# Load the employee data from the JSON file
try:
    with open("employees.json", "r") as f:
        # Load the entire JSON object, which is a dictionary with a key "employees"
        raw_data = json.load(f)
        # Extract the list of employees from the "employees" key
        employees_data = raw_data["employees"]
except (FileNotFoundError, KeyError) as e:
    print(f"Error loading employee data: {e}. Please check your employees.json file.")
    employees_data = []

# Initialize the Sentence Transformer model to create embeddings
model = SentenceTransformer('all-MiniLM-L6-v2') 

# Prepare the data for embedding by creating a single text document per employee
employee_docs = [
    f"Name: {emp['name']}. Skills: {', '.join(emp['skills'])}. Experience: {emp['experience_years']} years. Projects: {', '.join(emp['projects'])}."
    for emp in employees_data
]

# Create embeddings (vectors) for each employee document
print("Creating embeddings for employee data...")
employee_embeddings = model.encode(employee_docs)
print("Embeddings created.")

# Build the FAISS vector index for fast similarity search
d = employee_embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(np.array(employee_embeddings).astype('float32'))
print("FAISS index created with", index.ntotal, "vectors.")

# --- 3. FASTAPI APPLICATION ENDPOINTS ---
app = FastAPI()

origins = [
    "http://localhost",
    "https://chatbot-assignment-beige.vercel.app"
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def chat_with_rag(request: ChatRequest):
    """
    Handles a user's query using a simplified RAG system with smart formatting.
    """
    try:
        # a. Retrieval: Find relevant employees using the FAISS index
        query_embedding = model.encode([request.query])
        distances, indices = index.search(np.array(query_embedding).astype('float32'), k=3)
        
        retrieved_employees = [employees_data[i] for i in indices[0]]
        
        # Get the number of candidates found
        num_candidates = len(retrieved_employees)


        # b. Generation (Mnaual Formatting): Create a response string from the retrieved data
        if num_candidates == 0:
            return {"response": "I couldn't find any employees matching that query."}

        response_lines = []

        # Use a dynamic introductory sentence
        candidate_word = "candidate" if num_candidates == 1 else "candidates"

        # --Expertise detection
        expertise_keywords = [
            "machine learning", "ml", "deep learning", "ai", "artificial intelligence",
            "frontend", "backend", "fullstack", "devops", "cloud", "data science", "nlp",
            "computer vision", "cybersecurity", "mobile development", "blockchain"
        ]
        query_lower = request.query.lower()
        expertise_found = None
        for keyword in expertise_keywords:
            if keyword in query_lower:
                expertise_found = keyword
                break

        if expertise_found: 
            if expertise_found == "ml":
                expertise_found = "ML"
            else:
                expertise_found = expertise_found.title()

        # --- Domain detection
        domain_keywords = [
            "healthcare", "finance", "banking", "education", "ecommerce", "cloud",
            "iot", "logistics", "retail", "manufacturing", "gaming"
        ]

        domain_found = None
        for keyword in domain_keywords:
            if keyword in query_lower:
                domain_found = keyword
                break

        # Fallback: detect domain from projects
        if not domain_found:
            detected_domains = set()
            for emp in retrieved_employees:
                for proj in emp['projects']:
                    proj_lower = proj.lower()
                    for keyword in domain_keywords:
                        if keyword in proj_lower:
                            detected_domains.add(keyword)

            if detected_domains:
                domain_found = list(detected_domains)[0]

        #---Intro line
        if expertise_found and domain_found:
            intro_line = f"Based on your requirements for {expertise_found} expertise in {domain_found}, I found {num_candidates} excellent {candidate_word}:"
        elif expertise_found:
            intro_line = f"Based on your requirements for {expertise_found} expertise, I found {num_candidates} excellent {candidate_word}:"
        elif domain_found: 
            intro_line = f"Based on your requirements in {domain_found}, I found {num_candidates} excellent {candidate_word}:"
        else:
            intro_line = f"Based on your requirements, I found {num_candidates} excellent {candidate_word}:"

        response_lines = [intro_line]
        

        #---Candidate details
        for idx, emp in enumerate(retrieved_employees):
            pronoun = "He" if emp.get('gender') == 'male' else "She"
            possessive = "His" if emp.get('gender') == 'male' else "Her"

            if idx == 0:
                #First candidate
                text = (
                    f"**{emp['name']}** would be perfect for this role. "
                    f"{pronoun} has {emp['experience_years']} years of experience "
                    f"and is skilled in {', '.join(emp['skills'])}. "
                    f"{possessive} projects include: {', '.join(emp['projects'])}. "
                    f"{pronoun} is currently {emp['availability']}."
                )
            else:
                #Subsequent candidates
                text = (
                    f"**{emp['name']}** is another strong candidate with {emp['experience_years']} years of experience. "
                    f"{pronoun} knows {', '.join(emp['skills'])} "
                    f"and has worked on {', '.join(emp['projects'])}. "
                    f"{pronoun} is currently {emp['availability']}."
                )
            response_lines.append(text)

        #---Closing 
        if num_candidates == 1:
            closing = (
                f"This candidate has the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )
        elif num_candidates == 2:
            closing = (
                f"Both have the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )
        else: 
            closing = (
                f"All of them have the technical depth and domain expertise you need. "
                f"Would you like me to provide more details about their specific {domain_found or 'projects'} projects "
                f"or check their availability for meetings?"
            )

        response_lines.append(closing)        

        return {"response": "\n\n".join(response_lines)}

    except Exception as e:
        print(f"An error occurred in the chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/employees/search")
def search_employees(query: str):
    """
    A simple search endpoint for employees based on keywords in their skills, projects, and name.
    """
    found_employees = []
    query_lower = query.lower()

    for emp in employees_data:
        if (query_lower in emp['name'].lower() or
            any(query_lower in skill.lower() for skill in emp['skills']) or
            any(query_lower in proj.lower() for proj in emp['projects'])):
            found_employees.append(emp)
    
    return {"results": found_employees}