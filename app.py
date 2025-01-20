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
    Process a single query condition and return matching documents along with the condition.
    - AND: Documents must contain both terms.
    - OR: Documents must contain either term.
    - NOT: Exclude all documents containing the second term (ignore first term).
    - unused: Ignore the condition.
    """
    term1_set = search_term(term1) if term1 else set()
    term2_set = search_term(term2) if term2 else set()

    result = set()
    condition_type = f"{term1} {operator} {term2}"

    if operator == "AND":
        result = term1_set & term2_set
    elif operator == "OR":
        result = term1_set | term2_set
    elif operator == "NOT":
        result = all_doc_ids - term2_set  # Exclude all documents with Term 2
    elif operator == "unused":
        result = set()  # No results for unused conditions
        condition_type = None
    else:
        result = set()

    return result, condition_type

def generate_snippet(doc_id, terms):
    """Generate a document snippet with query terms highlighted and show surrounding words."""
    content = doc_contents.get(doc_id, "")  # Retrieve the document content
    if not content:
        return "Document not found."

    words = content.split()
    snippets = []

    # Iterate through each term to highlight it and show the context
    for term in terms:
        term = term.lower()  # Ensure case-insensitive matching
        term_positions = [i for i, word in enumerate(words) if word.lower() == term]
        
        for pos in term_positions:
            start = max(0, pos - 10)  # Get 10 words before (if possible)
            end = min(len(words), pos + 11)  # Get 10 words after (if possible)
            
            # Extract context around the term
            context = words[start:end]
            
            # Highlight the term in the context
            highlighted_context = [
                f"<b>{word}</b>" if word.lower() == term else word
                for word in context
            ]
            
            # Join the words and add the snippet
            snippets.append(" ".join(highlighted_context))

    # If snippets were generated, join them together
    if snippets:
        return " ... ".join(snippets) + " ..."
    else:
        return "No snippet available."




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
        document_conditions_matched = defaultdict(list)  # Track conditions matched for each document

        for term1, operator, term2 in conditions:
            result, condition_type = process_query(term1, operator, term2)
            if result:
                query_results.append((term1, operator, term2, result))
                for doc_id in result:
                    document_match_count[doc_id] += 1  # Increment match count per document
                    if condition_type:
                        document_conditions_matched[doc_id].append(condition_type)  # Store the condition
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
            doc_term_matrix=doc_term_matrix,
            document_conditions_matched=document_conditions_matched  # Pass conditions matched
        )

    return render_template("index.html")




if __name__ == "__main__":
    build_document_term_matrix()
    app.run(debug=True)