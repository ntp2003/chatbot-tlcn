from deepeval.test_case import LLMTestCase, ConversationalTestCase
from repositories.faq import get_all as get_all_faqs
from models.faq import FAQModel
import json
from typing import List, Dict
import random
import openai
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Define conversation starters
CONVERSATION_STARTERS = [
    "Chào shop, mình muốn hỏi về {topic}",
    "Shop ơi, cho mình hỏi về {topic}",
    "Mình đang tìm hiểu về {topic}",
    "Bên shop có {topic} không?",
    "Mình muốn hỏi về {topic}"
]

# Define follow-up questions
FOLLOW_UP_QUESTIONS = [
    "Vậy {topic} có {detail} không?",
    "Có thể cho mình biết thêm về {detail} không?",
    "Vậy {topic} thì {detail} thế nào?",
    "Có thể giải thích rõ hơn về {detail} không?",
    "Vậy {topic} có {detail} không shop?"
]

def generate_bot_response(user_message: str, faqs: List[FAQModel], turn_number: int) -> str:
    """Generate a bot response based on user message and FAQs"""
    if turn_number == 1:
        # First turn - greeting and asking for more information
        return f"Dạ chào anh/chị, em có thể giúp gì cho anh/chị ạ?"
    else:
        # Follow-up turns - provide information based on FAQs
        # Use OpenAI to generate a response based on the user message and FAQs
        faq_context = "\n".join([
            f"Q: {faq.question}\nA: {faq.answer}"
            for faq in faqs
        ])
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"""You are a helpful customer service representative at FPT Shop. 
                Use the following FAQs to answer customer questions:
                {faq_context}
                
                Guidelines:
                - Be professional and friendly
                - Use appropriate Vietnamese pronouns (em-anh/chị)
                - Keep responses concise but informative
                - If the question isn't covered in FAQs, ask for more details"""},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return response.choices[0].message.content

def generate_conversation_test_case(faqs: List[FAQModel], num_turns: int = 2) -> ConversationalTestCase:
    """Generate a multi-turn conversation test case"""
    # Select random FAQ
    faq = random.choice(faqs)
    
    # Generate conversation turns
    turns = []
    
    # First turn
    first_input = random.choice(CONVERSATION_STARTERS).format(topic=faq.title)
    first_output = generate_bot_response(first_input, [faq], 1)
    turns.append(LLMTestCase(
        input=first_input,
        actual_output=first_output,
        context=[f"FAQ Category: {faq.category}"]
    ))
    
    # Follow-up turns
    for i in range(1, num_turns):
        # Extract key details from FAQ answer for follow-up questions
        follow_up = random.choice(FOLLOW_UP_QUESTIONS).format(
            topic=faq.title,
            detail=random.choice(faq.answer.split(".")[0].split())
        )
        bot_response = generate_bot_response(follow_up, [faq], i + 1)
        turns.append(LLMTestCase(
            input=follow_up,
            actual_output=bot_response,
            context=[f"FAQ Category: {faq.category}"]
        ))
    
    return ConversationalTestCase(turns=turns)

def generate_test_cases(num_cases: int = 10, min_turns: int = 2, max_turns: int = 4) -> List[ConversationalTestCase]:
    """Generate multiple test cases using FAQs"""
    all_test_cases = []
    faqs = get_all_faqs()
    
    for _ in range(num_cases):
        num_turns = random.randint(min_turns, max_turns)
        test_case = generate_conversation_test_case(faqs, num_turns)
        all_test_cases.append(test_case)
    
    return all_test_cases

def save_test_cases(test_cases: List[ConversationalTestCase], output_file: str):
    """Save test cases to a JSON file"""
    serialized_cases = []
    for case in test_cases:
        serialized_turns = []
        for turn in case.turns:
            serialized_turns.append({
                "input": turn.input,
                "actual_output": turn.actual_output,
                "context": turn.context
            })
        serialized_cases.append({"turns": serialized_turns})
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serialized_cases, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Generate test cases
    test_cases = generate_test_cases(
        num_cases=10,  # 10 test cases
        min_turns=2,   # Minimum 2 turns per conversation
        max_turns=4    # Maximum 4 turns per conversation
    )
    
    # Save test cases
    save_test_cases(test_cases, "faq_conversation_test_cases.json")
    
    print(f"Generated {len(test_cases)} test cases")
    print("Test cases saved to faq_conversation_test_cases.json")
    
    # Example of how to use the test cases with DeepEval
    from deepeval import evaluate
    from deepeval.metrics import ConversationalGEval
    
    # Create evaluation metric
    faq_evaluation_metric = ConversationalGEval(
        name="FAQ Response Quality",
        criteria=[
            "Accurate information based on FAQs",
            "Appropriate use of Vietnamese pronouns",
            "Professional and friendly tone",
            "Clear and concise responses",
            "Natural conversation flow"
        ]
    )
    
    # Run evaluation
    evaluation_results = evaluate(
        test_cases=test_cases,
        metrics=[faq_evaluation_metric]
    )
    
    print("\nEvaluation Results:")
    print(evaluation_results) 