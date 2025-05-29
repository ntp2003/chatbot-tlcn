import os
import json
import time
from typing import List, Dict, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from test_sets.pronoun_test import load_test_cases as load_pronoun_tests
from test_sets.functionality_test import load_functionality_test_cases
from test_sets.tone_test import load_tone_test_cases
from metrics.evaluation_metrics import (
    calculate_overall_metrics,
    save_metrics,
    compare_metrics,
    EvaluationMetrics
)

def load_model(model_path: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load model và tokenizer
    """
    model = AutoModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    return model, tokenizer

def evaluate_model(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    test_cases: List[Dict],
    is_pronoun_test: bool = True
) -> Tuple[List[Dict], List[float]]:
    """
    Đánh giá model với test cases
    """
    results = []
    response_times = []
    
    for test_case in test_cases:
        start_time = time.time()
        
        # Tokenize input
        inputs = tokenizer(
            test_case.user_message,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        end_time = time.time()
        response_time = end_time - start_time
        response_times.append(response_time)
        
        # Evaluate based on test type
        if is_pronoun_test:
            from test_sets.pronoun_test import evaluate_pronoun_usage
            result = evaluate_pronoun_usage(response, test_case)
        else:
            from test_sets.functionality_test import evaluate_functionality
            result = evaluate_functionality(response, test_case)
            
        results.append(result)
        
    return results, response_times

def main():
    # Đường dẫn đến model trước và sau khi fine-tuning
    base_model_path = "path/to/base/model"
    fine_tuned_model_path = "path/to/fine-tuned/model"
    
    # Load test cases
    pronoun_test_cases = load_pronoun_tests()
    functionality_test_cases = load_functionality_test_cases()
    tone_test_cases = load_tone_test_cases()
    
    # Đánh giá model gốc
    print("Evaluating base model...")
    base_model, base_tokenizer = load_model(base_model_path)
    
    base_pronoun_results, base_pronoun_times = evaluate_model(
        base_model, base_tokenizer, pronoun_test_cases, is_pronoun_test=True
    )
    base_functionality_results, base_functionality_times = evaluate_model(
        base_model, base_tokenizer, functionality_test_cases, is_pronoun_test=False
    )
    base_tone_results, base_tone_times = evaluate_model(
        base_model, base_tokenizer, tone_test_cases, is_pronoun_test=False
    )
    
    base_metrics = calculate_overall_metrics(
        base_pronoun_results,
        base_functionality_results,
        base_tone_results,
        base_pronoun_times + base_functionality_times + base_tone_times
    )
    
    # Đánh giá model sau fine-tuning
    print("Evaluating fine-tuned model...")
    fine_tuned_model, fine_tuned_tokenizer = load_model(fine_tuned_model_path)
    
    fine_tuned_pronoun_results, fine_tuned_pronoun_times = evaluate_model(
        fine_tuned_model, fine_tuned_tokenizer, pronoun_test_cases, is_pronoun_test=True
    )
    fine_tuned_functionality_results, fine_tuned_functionality_times = evaluate_model(
        fine_tuned_model, fine_tuned_tokenizer, functionality_test_cases, is_pronoun_test=False
    )
    fine_tuned_tone_results, fine_tuned_tone_times = evaluate_model(
        fine_tuned_model, fine_tuned_tokenizer, tone_test_cases, is_pronoun_test=False
    )
    
    fine_tuned_metrics = calculate_overall_metrics(
        fine_tuned_pronoun_results,
        fine_tuned_functionality_results,
        fine_tuned_tone_results,
        fine_tuned_pronoun_times + fine_tuned_functionality_times + fine_tuned_tone_times
    )
    
    # Lưu kết quả
    os.makedirs("evaluation/results", exist_ok=True)
    save_metrics(base_metrics, "evaluation/results/base_metrics.json")
    save_metrics(fine_tuned_metrics, "evaluation/results/fine_tuned_metrics.json")
    
    # So sánh kết quả
    comparison = compare_metrics(base_metrics, fine_tuned_metrics)
    with open("evaluation/results/comparison.json", 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print("\nEvaluation Results:")
    print(f"Base Model Metrics: {base_metrics}")
    print(f"Fine-tuned Model Metrics: {fine_tuned_metrics}")
    print(f"Improvements: {comparison}")

if __name__ == "__main__":
    main() 