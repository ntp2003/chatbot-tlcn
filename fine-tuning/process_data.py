import json
import sys
from pathlib import Path

def fix_jsonl(input_path: str, output_path: str):
    """Fix and validate JSONL file."""
    fixed_data = []
    errors = []
    
    print(f"Processing {input_path}...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                # Remove any BOM characters
                line = line.strip().lstrip('\ufeff')
                if not line:  # Skip empty lines
                    continue
                    
                data = json.loads(line)
                # Validate required fields
                if "messages" not in data:
                    errors.append(f"Line {i}: Missing 'messages' field")
                    continue
                    
                messages = data["messages"]
                if not isinstance(messages, list):
                    errors.append(f"Line {i}: 'messages' is not a list")
                    continue
                
                # Extract system message, user query and assistant response
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
                user_msg = next((m["content"] for m in messages if m["role"] == "user"), None)
                assistant_msg = next((m["content"] for m in messages if m["role"] == "assistant"), None)
                
                if not all([system_msg, user_msg, assistant_msg]):
                    errors.append(f"Line {i}: Missing required message roles")
                    continue
                
                # Convert to training format
                fixed_data.append({
                    "instruction": f"Ngữ cảnh: {user_msg}\nYêu cầu: Trả lời với xưng hô phù hợp",
                    "input": "",
                    "output": assistant_msg
                })
                
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: JSON decode error - {str(e)}")
            except Exception as e:
                errors.append(f"Line {i}: Unexpected error - {str(e)}")
    
    # Save fixed data
    print(f"Writing processed data to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in fixed_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Report results
    print(f"\nProcessed {len(fixed_data)} valid examples")
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)
    
    return len(fixed_data), len(errors)

if __name__ == "__main__":
    input_file = "fine-tuning_data/tone1.jsonl"
    output_file = "training_data.jsonl"
    
    valid_count, error_count = fix_jsonl(input_file, output_file)
    
    if error_count == 0:
        print("\nData processing completed successfully!")
    else:
        print(f"\nData processing completed with {error_count} errors.")
        print("Please check the error messages above.") 