"""
Main automation script for processing enquiry documents.
Monitors folders for new PDFs and processes them using Claude.
"""
import time
import os
import sys
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from extractors import extract_pdf_text, extract_docx_text
from llm_client import process_with_claude
from excel_ops import fill_excel_template

# Configuration
WATCH_DIRECTORY = "/Users/shumaelr/RealCode/Enquiry/2025.11.29R to Shumael - AI - BOQ, Sizing & SLD"

# Track processed files to avoid duplicates
processed_files = set()


class EnquiryHandler(FileSystemEventHandler):
    """Handles file system events for new PDF files."""
    
    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Only process PDF files
        if not filename.lower().endswith(".pdf"):
            return
            
        # Skip temporary files and already processed files
        if filename.startswith("~$") or filename.startswith("."):
            return
            
        if filepath in processed_files:
            return
            
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] NEW FILE DETECTED")
        print(f"File: {filename}")
        print(f"{'='*60}")
        
        # Wait for file to be fully written
        time.sleep(2)
        
        # Mark as processed
        processed_files.add(filepath)
        
        # Process the file
        try:
            process_workflow(filepath)
        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()


def find_prompt_file(folder_path: str) -> str | None:
    """Finds the prompt file (.docx) in the folder."""
    for f in os.listdir(folder_path):
        if "Prompt" in f and f.endswith(".docx") and not f.startswith("~$"):
            return os.path.join(folder_path, f)
    return None


def find_template_file(folder_path: str) -> str | None:
    """Finds the Excel template file in the folder."""
    for f in os.listdir(folder_path):
        if "Format" in f and f.endswith(".xlsx") and not f.startswith("~$"):
            return os.path.join(folder_path, f)
    return None


def process_workflow(pdf_path: str) -> bool:
    """
    Main workflow to process a PDF document.
    
    1. Find the prompt and template files in the same folder
    2. Extract text from the PDF
    3. Extract instructions from the prompt
    4. Send to Claude for processing
    5. Write results to Excel
    
    Args:
        pdf_path: Path to the PDF file to process.
        
    Returns:
        True if successful, False otherwise.
    """
    folder_path = os.path.dirname(pdf_path)
    folder_name = os.path.basename(folder_path)
    pdf_filename = os.path.basename(pdf_path)
    
    print(f"\nProcessing category: {folder_name}")
    print(f"PDF file: {pdf_filename}")
    
    # Step 1: Find prompt and template files
    prompt_file = find_prompt_file(folder_path)
    template_file = find_template_file(folder_path)
    
    if not prompt_file:
        print(f"ERROR: Could not find Prompt file in {folder_name}")
        print("Expected: A .docx file with 'Prompt' in the name")
        return False
        
    if not template_file:
        print(f"ERROR: Could not find Template file in {folder_name}")
        print("Expected: A .xlsx file with 'Format' in the name")
        return False
    
    print(f"Using Prompt: {os.path.basename(prompt_file)}")
    print(f"Using Template: {os.path.basename(template_file)}")
    
    # Step 2: Extract PDF text
    print("\n[Step 1/4] Extracting text from PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    
    if not pdf_text:
        print("ERROR: Failed to extract text from PDF")
        return False
    
    print(f"Extracted {len(pdf_text)} characters from PDF")
    
    # Step 3: Extract prompt instructions
    print("\n[Step 2/4] Reading prompt instructions...")
    prompt_text = extract_docx_text(prompt_file)
    
    if not prompt_text:
        print("WARNING: Could not read prompt file, using default instructions")
        prompt_text = "Extract all relevant technical data from this document."
    
    print(f"Loaded {len(prompt_text)} characters of instructions")
    
    # Step 4: Process with Claude
    print("\n[Step 3/4] Sending to Claude for analysis...")
    data = process_with_claude(pdf_text, prompt_text, category=folder_name)
    
    if not data:
        print("ERROR: Failed to get valid response from Claude")
        return False
    
    # Step 5: Generate output Excel
    print("\n[Step 4/4] Generating Excel output...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"Output_{pdf_filename.replace('.pdf', '')}_{timestamp}.xlsx"
    output_path = os.path.join(folder_path, output_filename)
    
    success = fill_excel_template(template_file, output_path, data)
    
    if success:
        print(f"\n{'='*60}")
        print("SUCCESS! Processing complete.")
        print(f"Output saved to: {output_filename}")
        print(f"{'='*60}\n")
        return True
    else:
        print("ERROR: Failed to generate Excel output")
        return False


def process_existing_files():
    """Process any existing PDF files that haven't been processed yet."""
    print("\nScanning for existing PDF files...")
    
    for folder_name in ["BOQ", "Sizing", "SLD"]:
        folder_path = os.path.join(WATCH_DIRECTORY, folder_name)
        
        if not os.path.exists(folder_path):
            continue
            
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf") and not filename.startswith("~$"):
                filepath = os.path.join(folder_path, filename)
                
                # Check if output already exists
                output_exists = False
                for f in os.listdir(folder_path):
                    if f.startswith("Output_") and filename.replace(".pdf", "") in f:
                        output_exists = True
                        break
                
                if not output_exists:
                    print(f"Found unprocessed: {filename}")


def main():
    """Main entry point."""
    print("="*60)
    print("ENQUIRY DOCUMENT PROCESSOR")
    print("="*60)
    print(f"Watch Directory: {WATCH_DIRECTORY}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Verify directory exists
    if not os.path.exists(WATCH_DIRECTORY):
        print(f"\nERROR: Directory not found: {WATCH_DIRECTORY}")
        print("Please update WATCH_DIRECTORY in this script.")
        sys.exit(1)
    
    # List monitored folders
    print("\nMonitoring folders:")
    for folder in ["BOQ", "Sizing", "SLD"]:
        folder_path = os.path.join(WATCH_DIRECTORY, folder)
        if os.path.exists(folder_path):
            print(f"  ✓ {folder}")
        else:
            print(f"  ✗ {folder} (not found)")
    
    # Check for existing unprocessed files
    process_existing_files()
    
    # Start watching
    event_handler = EnquiryHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=True)
    
    print("\n" + "="*60)
    print("READY - Waiting for new PDF files...")
    print("Drop a PDF into BOQ, Sizing, or SLD folder to process it.")
    print("Press Ctrl+C to stop.")
    print("="*60 + "\n")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        observer.stop()
        
    observer.join()
    print("Goodbye!")


if __name__ == "__main__":
    main()
