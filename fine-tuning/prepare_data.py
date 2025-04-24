import json
import pandas as pd
from typing import List, Dict

def create_instruction_dataset(conversations: List[Dict]) -> List[Dict]:
    """Convert conversations into instruction format."""
    dataset = []
    
    # Example conversation pairs with proper Vietnamese pronouns
    instruction_template = """
    Hãy trả lời với xưng hô phù hợp trong ngữ cảnh sau:
    Ngữ cảnh: {context}
    Người nói: {speaker_role}
    Người nghe: {listener_role}
    """
    
    for conv in conversations:
        context = conv["context"]
        speaker = conv["speaker_role"]
        listener = conv["listener_role"]
        response = conv["response"]
        
        instruction = instruction_template.format(
            context=context,
            speaker_role=speaker,
            listener_role=listener
        )
        
        dataset.append({
            "instruction": instruction.strip(),
            "input": "",
            "output": response
        })
    
    return dataset

def main():
    # Example conversation data
    conversations = [
        {
            "context": "Học sinh hỏi giáo viên về bài tập",
            "speaker_role": "học sinh",
            "listener_role": "giáo viên",
            "response": "Thưa cô, em có thắc mắc về bài tập này ạ."
        },
        {
            "context": "Giáo viên trả lời học sinh",
            "speaker_role": "giáo viên",
            "listener_role": "học sinh",
            "response": "Cô sẽ giải thích cho con nhé. Con hãy nói rõ phần nào con chưa hiểu."
        },
        # Add more examples here
    ]
    
    # Convert to instruction format
    dataset = create_instruction_dataset(conversations)
    
    # Save as JSONL
    with open("training_data.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"Created dataset with {len(dataset)} examples")

if __name__ == "__main__":
    main() 