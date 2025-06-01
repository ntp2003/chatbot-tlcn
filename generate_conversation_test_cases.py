from deepeval.test_case import LLMTestCase, ConversationalTestCase
from deepeval.synthesizer import Synthesizer
from deepeval.dataset import Golden
from deepeval.synthesizer.config import StylingConfig
import json
from typing import List, Dict
import random

# Define different gender contexts
GENDER_CONTEXTS = [
    "User gender: male",
    "User gender: female", 
    "User gender: unknown"
]

# Define expected pronouns for each gender
GENDER_PRONOUNS = {
    "male": {"bot": "em", "user": "anh"},
    "female": {"bot": "em", "user": "chị"},
    "unknown": {"bot": "em", "user": "anh/chị"}
}

# Define conversation starters
CONVERSATION_STARTERS = [
    "Chào shop, mình muốn hỏi về {product}",
    "Shop ơi, cho mình hỏi về {product}",
    "Mình đang tìm hiểu về {product}",
    "Bên shop có {product} không?",
    "Mình muốn mua {product}"
]

# Define follow-up questions
FOLLOW_UP_QUESTIONS = [
    "Nó có mấy màu vậy {bot_pronoun}?",
    "Giá bao nhiêu vậy {bot_pronoun}?",
    "Có khuyến mãi gì không {bot_pronoun}?",
    "Bảo hành thế nào vậy {bot_pronoun}?",
    "Có thể giao hàng tận nơi không {bot_pronoun}?",
    "Có trả góp được không {bot_pronoun}?",
    "Có thể đổi trả không {bot_pronoun}?",
    "Có hàng chính hãng không {bot_pronoun}?"
]

# Define products
PRODUCTS = [
    "iPhone 15",
    "Samsung Galaxy S24",
    "MacBook Pro",
    "iPad Pro",
    "AirPods Pro",
    "Apple Watch",
    "Sony WH-1000XM5",
    "Samsung TV"
]

def generate_bot_response(user_message: str, gender_context: str, turn_number: int) -> str:
    """Generate a bot response based on user message and gender context"""
    gender = gender_context.split(": ")[1].strip()
    pronouns = GENDER_PRONOUNS[gender]
    
    if turn_number == 1:
        # First turn - greeting and asking for more information
        return f"Dạ chào {pronouns['user']}, em có thể giúp gì cho {pronouns['user']} ạ?"
    else:
        # Follow-up turns - provide information and ask for more details
        return f"Dạ {pronouns['user']} có thể cho em biết thêm thông tin gì không ạ?"

def generate_conversation_test_case(gender_context: str, num_turns: int = 2) -> ConversationalTestCase:
    """Generate a multi-turn conversation test case"""
    gender = gender_context.split(": ")[1].strip()
    pronouns = GENDER_PRONOUNS[gender]
    
    # Select random product
    product = random.choice(PRODUCTS)
    
    # Generate conversation turns
    turns = []
    
    # First turn
    first_input = random.choice(CONVERSATION_STARTERS).format(product=product)
    first_output = generate_bot_response(first_input, gender_context, 1)
    turns.append(LLMTestCase(
        input=first_input,
        actual_output=first_output,
        context=[gender_context]
    ))
    
    # Follow-up turns
    for i in range(1, num_turns):
        follow_up = random.choice(FOLLOW_UP_QUESTIONS).format(bot_pronoun=pronouns["bot"])
        bot_response = generate_bot_response(follow_up, gender_context, i + 1)
        turns.append(LLMTestCase(
            input=follow_up,
            actual_output=bot_response,
            context=[gender_context]
        ))
    
    return ConversationalTestCase(turns=turns)

def generate_test_cases(num_cases_per_gender: int = 5, min_turns: int = 2, max_turns: int = 4) -> List[ConversationalTestCase]:
    """Generate multiple test cases for each gender context"""
    all_test_cases = []
    
    for gender_context in GENDER_CONTEXTS:
        for _ in range(num_cases_per_gender):
            num_turns = random.randint(min_turns, max_turns)
            test_case = generate_conversation_test_case(gender_context, num_turns)
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
        num_cases_per_gender=5,  # 5 test cases for each gender
        min_turns=2,            # Minimum 2 turns per conversation
        max_turns=4             # Maximum 4 turns per conversation
    )
    
    # Save test cases
    save_test_cases(test_cases, "conversation_test_cases.json")
    
    print(f"Generated {len(test_cases)} test cases")
    print("Test cases saved to conversation_test_cases.json")
    
    # Example of how to use the test cases with DeepEval
    from deepeval import evaluate
    from deepeval.metrics import ConversationalGEval
    
    # Create evaluation metric
    pronoun_evaluation_metric = ConversationalGEval(
        name="Vietnamese Pronoun Consistency",
        criteria=[
            "Proper use of gender-specific pronouns (em-anh, em-chị, em-anh/chị)",
            "Consistent pronoun usage throughout the conversation",
            "Appropriate level of formality based on gender context",
            "Natural and respectful tone"
        ]
    )
    
    # Run evaluation
    evaluation_results = evaluate(
        test_cases=test_cases,
        metrics=[pronoun_evaluation_metric]
    )
    
    print("\nEvaluation Results:")
    print(evaluation_results) 