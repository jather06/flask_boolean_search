from flask import Flask, render_template, request
from collections import defaultdict
import re
import os

app = Flask(__name__)

# Stopwords to exclude during preprocessing
STOPWORDS = ["a", "an", "the", "and", "or", "not", "in", "on", "at", "with", "by", "for", "is", "are", "of", "to", "as"]

documents = []
doc_term_matrix = defaultdict(set)  
all_doc_ids = set(range(1, 11)) 
doc_contents = {}


# Path to document directory (update this as needed)
DOC_DIR = "documents"

# Preprocesses text: converting lowercase, remove punctuation,  filter stopwords. Returns a list of the remaining words
def preprocess_text(text):
    """Lowercase, remove punctuation, and filter out stopwords."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    words = [word for word in text.split() if word not in STOPWORDS]
    return words

# Load documents, read documents, store document contents, populate the doc_term matrix with the filtered words (from function above)
def build_document_term_matrix():
    """Load and preprocess documents to build the term-document matrix."""
    global doc_contents

    for i in range(1, 11):
        doc_path = os.path.join(DOC_DIR, f"doc{i}.txt")
        if not os.path.exists(doc_path): 
            print(f"Warning: {doc_path} does not exist.")
            continue

        with open(doc_path, "r") as f:
            text = f.read()
            doc_contents[i] = text  

        words = preprocess_text(text)
        documents.append(" ".join(words))

        for word in words:
            doc_term_matrix[word].add(i)


# search for a term in the doc_term_matrix
def search_term(term):
    term = term.strip().lower()
    return doc_term_matrix.get(term, set())


def process_query(term1, operator, term2):
    """
    Process a single query condition and return matching documents along with the condition.
    - AND: Documents must contain both terms.
    - OR: Documents must contain either term.
    - NOT: Exclude all documents containing the second term (ignore first term)
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
        result = all_doc_ids - term2_set  # exclude all documents with Term 2
    elif operator == "unused":
        result = set()
        condition_type = None
    else:
        result = set()
    return result, condition_type

# Generate a document snippet with query terms highlighted
def generate_snippet(doc_id, terms):
    content = doc_contents.get(doc_id, "")  
    if not content: # error handling
        return "Document not found."

    words = content.split() # all the words, not filtered
    snippets = []

    # go through each term to highlight it and show the context
    for term in terms:
        term = term.lower()  # to ensure case-insensitive matching
        term_positions = []

        # find all instances of term 
        for i, word in enumerate(words):
            if word.lower() == term:
                term_positions.append(i)  
        # highlight term and show context
        for pos in term_positions:
            start = max(0, pos - 10)  # Get 10 words before (if possible)
            end = min(len(words), pos + 11)  # Get 10 words after (if possible)
            
            context = words[start:end]
            
            highlighted_context = [
                f"<b>{word}</b>" if word.lower() == term else word
                for word in context
            ]
            
            # Join the words and add the snippet
            snippets.append(" ".join(highlighted_context))

    # if snippets were generated, join them together
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
            conditions.append((term1, operator, term2)) # append set of conditions inside conditions list

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
                        document_conditions_matched[doc_id].append(condition_type)  # Store the matched condition
                if term1:
                    filtered_terms.add(term1.lower())
                if term2:
                    filtered_terms.add(term2.lower())

        # Rank documents by match count 
        ranked_documents = sorted(
            document_match_count.items(), key=lambda x: (-x[1]) # sort by match count (-x[1] makes it descending) and ascending docnames (x[0]) if there is a tie 
        )

        # Group results by match count
        match_summary = defaultdict(list)
        for doc_id, count in ranked_documents:
            match_summary[count].append(doc_id)
        
        # variables for the template
        return render_template(
            "results.html", 
            term1=term1,
            term2=term2,
            operator=operator,
            conditions=conditions,
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

build_document_term_matrix()

app.run(debug=True) 
