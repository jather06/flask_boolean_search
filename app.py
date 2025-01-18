from flask import Flask, render_template, request
import os
import string
from collections import defaultdict
import re

app = Flask(__name__)

# Stopwords to exclude during preprocessing
STOPWORDS = ["a", "an", "the", "and", "or", "not", "in", "on", "at", "with", "by", "for", "is", "are", "of", "to", "as"]

documents = []  # List to store preprocessed documents
doc_term_matrix = defaultdict(set)  # Dictionary to store the document-term matrix
doc_t_matrix1 = {}

def preprocess_and_read_documents():
    for i in range(1, 11):  # Assuming documents are named doc1.txt to doc10.txt
        with open(f"documents/doc{i}.txt", "r") as f:
            text = f.read()
            # Preprocessing: lowercasing and removing punctuation with regex
            text = text.lower()
            text = re.sub(r"[^\w\s]", "", text)  # Removes all characters except letters, digits, and whitespace
            
            # Removing stopwords and splitting into words
            words = [word for word in text.split() if word not in STOPWORDS]
            
            # Add the processed text to the documents list
            documents.append(" ".join(words))
            
            # Populate the document-term matrix
            for word in words:
                doc_term_matrix[word].add(i)  # Add the document ID (i) to the set of documents containing the word

preprocess_and_read_documents()

# Print the document-term matrix for verification
print("Document-Term Matrix:")
for term, doc_ids in doc_term_matrix.items():
    doc_t_matrix1[term]=doc_ids

    doc_t_mat = open("doc_term_matrix.txt", "a")
    doc_t_mat.write(f"{term}: {sorted(doc_ids)} # ")
print(doc_t_matrix1)
q1_res = []
def search_str(word):
        with open('doc_term_matrix.txt', 'r') as file:
            # read all content of a file
            content= file.read()
            # check if string present in a file
            for i in range(1,11):

                if f" {word}: [{i}" in content:
                    q1_res.append(i)

def process_queries():
    res = open("doc_term_matrix.txt", "r")

    query1 = input("query 1: ")
    if "AND" in query1:
        query1 = query1.split(" AND ")
        for i in query1:
            search_str(i)
        if 'False' not in q1_res:
            print("Query 1 has a hit")
process_queries()
print(q1_res)