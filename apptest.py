import os
import re
import logging
from collections import defaultdict

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Define stopwords
STOPWORDS = [
    "a", "an", "the", "and", "or", "not", "in", "on", "at", "with", "by", "for", "is", "are", "of", "to", "as"
]

# Initialize documents list and term matrix
documents = []
doc_term_matrix = defaultdict(set)

def preprocess_and_read_documents():
    """Read and preprocess documents from the 'documents/' directory."""
    for i in range(1, 11):
        file_path = f"documents/doc{i}.txt"
        logger.debug(f"Attempting to process: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Read file content
                text = f.read()
                logger.debug(f"Successfully read {file_path}")

                # Preprocessing: lowercasing and removing punctuation
                try:
                    text = text.lower()
                    text = re.sub(r"[^\w\s]", "", text)  # Removes all characters except letters, digits, and whitespace
                    processed_text = " ".join(word for word in text.split() if word not in STOPWORDS)
                    
                    # Add processed text to documents list
                    documents.append(processed_text)
                    logger.info(f"Successfully processed {file_path}")
                except Exception as preprocess_error:
                    logger.error(f"Error during preprocessing {file_path}: {preprocess_error}")

        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

# Call the function to process documents
preprocess_and_read_documents()

# Debug final output
logger.debug(f"Processed documents: {documents}")

print(doc_term_matrix)