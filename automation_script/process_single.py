"""
Utility script to process a single PDF file without running the watcher.
Usage: python process_single.py <path_to_pdf>
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import process_workflow, WATCH_DIRECTORY


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_single.py <path_to_pdf>")
        print("\nOr specify just the folder and filename:")
        print("  python process_single.py BOQ/01_Scope Of Supply.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # If relative path, try to resolve against watch directory
    if not os.path.isabs(pdf_path):
        full_path = os.path.join(WATCH_DIRECTORY, pdf_path)
        if os.path.exists(full_path):
            pdf_path = full_path
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.lower().endswith(".pdf"):
        print("Error: File must be a PDF")
        sys.exit(1)
    
    print(f"Processing: {pdf_path}")
    success = process_workflow(pdf_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
