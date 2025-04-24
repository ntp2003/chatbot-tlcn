import json
import sys
from pathlib import Path

def check_jsonl(file_path):
    """Check JSONL file line by line and report any issues."""
    print(f"Checking file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    print(f"Total lines in file: {len(lines)}")
    
    valid_lines = []
    errors = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            print(f"Line {i}: Empty line")
            continue
            
        try:
            # Try to parse JSON
            data = json.loads(line)
            valid_lines.append(data)
            
            # Validate structure
            if "messages" not in data:
                print(f"Line {i}: Missing 'messages' field")
                continue
                
            messages = data["messages"]
            if not isinstance(messages, list):
                print(f"Line {i}: 'messages' is not a list")
                continue
                
            # Check required message types
            roles = [m.get("role") for m in messages]
            if not all(role in roles for role in ["system", "user", "assistant"]):
                print(f"Line {i}: Missing required message roles")
                continue
                
        except json.JSONDecodeError as e:
            print(f"Line {i}: JSON decode error")
            print(f"Error details: {str(e)}")
            print(f"Problematic line content (first 100 chars): {line[:100]}")
            errors.append((i, str(e), line))
        except Exception as e:
            print(f"Line {i}: Unexpected error: {str(e)}")
            errors.append((i, str(e), line))
    
    print(f"\nSummary:")
    print(f"Total valid JSON objects: {len(valid_lines)}")
    print(f"Total errors: {len(errors)}")
    
    if errors:
        print("\nDetailed error information:")
        for line_num, error, content in errors:
            print(f"\nLine {line_num}:")
            print(f"Error: {error}")
            print(f"Content preview: {content[:100]}...")
    
    return valid_lines, errors

if __name__ == "__main__":
    file_path = "fine-tuning_data/tone1.jsonl"
    valid_lines, errors = check_jsonl(file_path)
    
    if not errors:
        print("\nFile format is valid!") 