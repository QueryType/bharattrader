import os
from PyPDF2 import PdfReader
from transformers import PegasusTokenizer, PegasusForConditionalGeneration

#path of the folder where your pdfs are located
folder_path = "concallpdfs" 

# Max token size
max_seq_length = 512

# Max token for pegasus financial summarization
max_length_pegasus_fin_summ = 32

# Pick model
# model_name = "google/pegasus-xsum" -- used for testing
model_name = "human-centered-summarization/financial-summarization-pegasus"

# Load pretrained tokenizer
pegasus_tokenizer = PegasusTokenizer.from_pretrained(model_name)

# Make model from pre-trained model
model = PegasusForConditionalGeneration.from_pretrained(model_name)

for filename in os.listdir(folder_path):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(folder_path, filename)
        with open(pdf_path, "rb") as file:
            print(f'Summarizing {filename}')
            reader = PdfReader(file)
            page_summaries = []
            count = 0
            for page in reader.pages: # summarize page by page
                page_text = page.extract_text()
                # Generate input tokens
                input_ids = pegasus_tokenizer(page_text,  max_length=max_seq_length, truncation=True, return_tensors="pt").input_ids
                # Generate Summary
                summary_ids = model.generate(input_ids, max_length=max_length_pegasus_fin_summ, num_beams=5, early_stopping=True)
                tgt_texts = pegasus_tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
                page_summaries.append(tgt_texts[0])
                count = count + 1
                # print(f'{count} page(s) done')
            # Merge all page summaries
            merged_summary = "\n".join(page_summaries)
            # Write the merged summary to a file
            with open(f'{folder_path}/{filename}_summary.txt', 'w') as f:
                f.write(merged_summary)
        print(f'{filename} done')
