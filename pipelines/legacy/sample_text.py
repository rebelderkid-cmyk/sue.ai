import json
import random
import sys

def extract_sample(input_file, output_file, sample_size=50):
    all_lines = []
    with open(input_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    # Sample lines
    if len(all_lines) > sample_size:
        # Get a mix of start, middle, end, + random
        # Just random is fine if distribution is uniform
        sample_indices = sorted(random.sample(range(len(all_lines)), sample_size))
        sampled_lines = [all_lines[i] for i in sample_indices]
    else:
        sampled_lines = all_lines
    
    with open(output_file, 'w', encoding='utf-8') as out:
        for idx, line in enumerate(sampled_lines):
            try:
                data = json.loads(line)
            except:
                continue
                
            pdf_file = data.get('pdf_file', f'Unknown_{idx}')
            out.write(f"--- Document: {pdf_file} ---\n")
            
            # Extract text
            raw_text = ""
            inner_data = data.get('data', {})
            if inner_data:
                raw_results = inner_data.get('raw_results', [])
                for page in raw_results:
                    raw_text += f"[Page {page.get('page_num')}]\n"
                    raw_text += page.get('raw_output', '') + "\n"
            else:
                 raw_text = data.get('raw_text', '')

            out.write(raw_text)
            out.write("\n\n" + "="*50 + "\n\n")

if __name__ == "__main__":
    extract_sample("downloads/2016/2016-01.jsonl", "sample_dump.txt")
