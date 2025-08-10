HR Resource Query Chatbot
An intelligent chatbot designed to help HR managers query an employee database for technical skills, experience, and projects.

##Overview
This project implements a Retrieval-Augmented Generation (RAG) system to provide highly relevant and customized responses to natural language queries. The backend uses a "Simple RAG" approach, combining vector similarity search for retrieval with advanced manual formatting for response generation, eliminating the need for a costly or resource-intensive Large Language Model.

##Features
1. Semantic Search: Uses vector embeddings to find the most relevant employees for a given query, moving beyond simple keyword matching.
2. Dynamic Response Generation: Constructs natural-language responses that are highly customized based on the retrieved data.
3. Robust Data Handling: Loads employee data from a local JSON file to build a searchable index on startup.
4. Correct Pronoun Usage: Uses a gender field in the dataset to ensure grammatically correct and respectful pronoun usage.
5. RESTful API: Provides a clean and easy-to-use API for a frontend application to consume.

Basic Error Handling: Implements try-except blocks and Pydantic validation to ensure API stability.

