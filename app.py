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
doc_contents = {}  # Dictionary to store the original content of each document


# Path to document directory (update this as needed)
DOC_DIR = "documents"

def preprocess_text(text):
    """Lowercase, remove punctuation, and filter out stopwords."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    words = [word for word in text.split() if word not in STOPWORDS]
    return words

def build_document_term_matrix():
    """Load and preprocess documents to build the term-document matrix."""
    global doc_contents  # Ensure we use the global doc_contents variable

    for i in range(1, 11):  # Assuming document files are named doc1.txt to doc10.txt
        doc_path = os.path.join(DOC_DIR, f"doc{i}.txt")
        if not os.path.exists(doc_path):
            print(f"Warning: {doc_path} does not exist.")
            continue

        # Read the document content
        with open(doc_path, "r") as f:
            text = f.read()
            doc_contents[i] = text  # Store the original content of the document

        # Preprocess the text
        words = preprocess_text(text)
        documents.append(" ".join(words))

        # Populate the term-document matrix
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

def generate_snippet(doc_id, terms, document_match_count):
    """Generate a document snippet with query terms highlighted, showing context before and after the term."""
    # If no matches for the document, return an empty string
    if document_match_count.get(doc_id, 0) == 0:
        return ""

    content = doc_contents.get(doc_id, "")  # Retrieve the document content
    if not content:
        return "Document not found."

    words = content.split()
    highlighted_words = set(terms)  # Set of terms to highlight
    snippets = []

    # Loop through words to find terms and generate snippets
    for i, word in enumerate(words):
        # If the word matches any of the terms, generate a snippet
        if any(re.search(rf"\b{re.escape(term)}\b", word, re.IGNORECASE) for term in highlighted_words):
            # Define the context around the found term (10 words before, 10 after)
            start = max(i - 10, 0)
            end = min(i + 11, len(words))

            # Create a snippet with the surrounding words
            snippet_context = words[start:end]
            # Bold the found term in the snippet context
            snippet_context = [
                f"<b>{word}</b>" if any(re.search(rf"\b{re.escape(term)}\b", word, re.IGNORECASE) for term in highlighted_words) else word
                for word in snippet_context
            ]
            snippets.append(" ".join(snippet_context))

    # If no terms were found in the document, return empty
    if not snippets:
        return ""

    # Return all snippets joined together
    return " ... ".join(snippets)




@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Retrieve query conditions from the form
        conditions = []
        for i in range(1, 5):
            term1 = request.form.get(f"term1_{i}", "").strip()
            operator = request.form.get(f"operator_{i}", "unused")
            term2 = request.form.get(f"term2_{i}", "").strip()
            conditions.append((term1, operator, term2))

        # Process each condition and calculate results
        query_results = []
        document_match_count = defaultdict(int)  # Count matches per document
        filtered_terms = set()

        for term1, operator, term2 in conditions:
            result = process_query(term1, operator, term2)
            if result is not None:  # Only store results for valid conditions
                query_results.append((term1, operator, term2, result))
                for doc_id in result:
                    document_match_count[doc_id] += 1  # Increment match count per document
                if term1:
                    filtered_terms.add(term1.lower())
                if term2:
                    filtered_terms.add(term2.lower())

        # Rank documents by match count (descending order)
        ranked_documents = sorted(
            document_match_count.items(), key=lambda x: (-x[1], x[0])
        )

        # Group results by match count
        match_summary = defaultdict(list)
        for doc_id, count in ranked_documents:
            match_summary[count].append(doc_id)

        return render_template(
            "results.html",
            query_results=query_results,
            ranked_documents=ranked_documents,
            match_summary=match_summary,
            filtered_terms=filtered_terms,
            generate_snippet=generate_snippet,
            document_match_count=document_match_count,
            doc_term_matrix=doc_term_matrix  # Ensure doc_term_matrix is passed
        )

    return render_template("index.html")



if __name__ == "__main__":
    build_document_term_matrix()
    app.run(debug=True)