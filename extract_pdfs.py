
import os
import pypdf

pdf_dir = "Visual Research"
output_file = "visual_research_content.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for filename in sorted(os.listdir(pdf_dir)):
        if filename.endswith(".pdf"):
            filepath = os.path.join(pdf_dir, filename)
            try:
                reader = pypdf.PdfReader(filepath)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                out.write(f"--- START OF {filename} ---\n")
                out.write(text)
                out.write(f"--- END OF {filename} ---\n\n")
                print(f"Extracted {filename}")
            except Exception as e:
                print(f"Failed to read {filename}: {e}")
