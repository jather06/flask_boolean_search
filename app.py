from flask import Flask, render_template, request
from collections import defaultdict
import re
import os

app = Flask(__name__)

# Stopwords to exclude during preprocessing
STOPWORDS = {"a", "an", "the", "and", "or", "not", "in", "on", "at", "with", "by", "for", "is", "are", "of", "to", "as"}

documents = []  # List to store preprocessed documents
doc_term_matrix = defaultdict(set)  # Dictionary to store the document-term matrix
all_doc_ids = set(range(1, 11))  # Assuming there are 10 documents named doc1.txt to doc10.txt

# Path to document directory (update this as needed)
DOC_DIR = "documents"

def preprocess_text(text):
    """Lowercase, remove punctuation, and filter out stopwords."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    words = [word for word in text.split() if word not in STOPWORDS]
    return words

def build_document_term_matrix():
    """Read documents, preprocess them, and build the term-document matrix."""
    for i in range(1, 11):  # Assuming documents are named doc1.txt to doc10.txt
        doc_path = os.path.join(DOC_DIR, f"doc{i}.txt")
        if not os.path.exists(doc_path):
            continue

        with open(doc_path, "r") as f:
            text = f.read()

        # Preprocess the text
        words = preprocess_text(text)
        documents.append(" ".join(words))

        # Update the document-term matrix
        for word in words:
            doc_term_matrix[word].add(i)

def search_term(term):
    """Search for a term in the document-term matrix."""
    term = term.strip().lower()
    return doc_term_matrix.get(term, set())

def process_query(term1, operator, term2):
    """
    Process a single query condition.
    - AND: Documents must contain both terms.
    - OR: Documents must contain either term.
    - NOT: Exclude all documents containing the second term (ignore first term).
    - unused: Ignore the condition.
    """
    term1_set = search_term(term1) if term1 else set()
    term2_set = search_term(term2) if term2 else set()

    if operator == "AND":
        return term1_set & term2_set
    elif operator == "OR":
        return term1_set | term2_set
    elif operator == "NOT":
        return all_doc_ids - term2_set  # Exclude all documents with Term 2
    elif operator == "unused":
        return None  # Ignore unused condition
    else:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    query_results = []  # To store individual results for each condition
    combined_result = all_doc_ids  # Start with all documents for intersection

    if request.method == "POST":
        # Retrieve query conditions from the form
        conditions = []
        for i in range(1, 5):
            term1 = request.form.get(f"term1_{i}", "").strip()
            operator = request.form.get(f"operator_{i}", "unused")
            term2 = request.form.get(f"term2_{i}", "").strip()
            conditions.append((term1, operator, term2))

        # Process each condition and store individual results
        for idx, (term1, operator, term2) in enumerate(conditions):
            result = process_query(term1, operator, term2)
            if result is not None:  # Only store results for valid conditions
                query_results.append((idx + 1, term1, operator, term2, sorted(result)))
                combined_result &= result  # Intersect with the combined result

    return render_template("index.html", query_results=query_results, combined_result=sorted(combined_result))

if __name__ == "__main__":
    build_document_term_matrix()
    app.run(debug=True)
