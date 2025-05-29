import json
from typing import List, Dict
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EvaluationMetrics:
    pronoun_accuracy: float
    functionality_accuracy: float
    tone_accuracy: float
    response_time: float
    consistency_score: float
    timestamp: str

def calculate_pronoun_metrics(results: List[Dict]) -> Dict:
    """
    Tính toán các metrics cho việc sử dụng đại từ
    """
    total_cases = len(results)
    if total_cases == 0:
        return {
            "accuracy": 0.0,
            "consistency": 0.0
        }
        
    correct_pronouns = sum(1 for r in results if r["correct_pronouns"])
    consistent_pronouns = sum(1 for r in results if r["consistent_pronouns"])
    
    return {
        "accuracy": correct_pronouns / total_cases,
        "consistency": consistent_pronouns / total_cases
    }

def calculate_functionality_metrics(results: List[Dict]) -> Dict:
    """
    Tính toán các metrics cho chức năng
    """
    total_cases = len(results)
    if total_cases == 0:
        return {
            "product_type_accuracy": 0.0,
            "intent_accuracy": 0.0,
            "relevance_score": 0.0
        }
        
    correct_product_types = sum(1 for r in results if r["correct_product_type"])
    correct_intents = sum(1 for r in results if r["correct_intent"])
    relevant_responses = sum(1 for r in results if r["response_relevance"])
    
    return {
        "product_type_accuracy": correct_product_types / total_cases,
        "intent_accuracy": correct_intents / total_cases,
        "relevance_score": relevant_responses / total_cases
    }

def calculate_tone_metrics(results: List[Dict]) -> Dict:
    """
    Tính toán các metrics cho tone
    """
    total_cases = len(results)
    if total_cases == 0:
        return {
            "tone_match_rate": 0.0,
            "keyword_presence_rate": 0.0,
            "average_response_length": 0.0
        }
        
    tone_matches = sum(1 for r in results if r["tone_match"])
    keyword_presence = sum(r["keyword_presence"] for r in results)
    response_lengths = [r["response_length"] for r in results]
    
    return {
        "tone_match_rate": tone_matches / total_cases,
        "keyword_presence_rate": keyword_presence / total_cases,
        "average_response_length": np.mean(response_lengths)
    }

def calculate_overall_metrics(
    pronoun_results: List[Dict],
    functionality_results: List[Dict],
    tone_results: List[Dict],
    response_times: List[float]
) -> EvaluationMetrics:
    """
    Tính toán tổng hợp các metrics
    """
    pronoun_metrics = calculate_pronoun_metrics(pronoun_results)
    functionality_metrics = calculate_functionality_metrics(functionality_results)
    tone_metrics = calculate_tone_metrics(tone_results)
    
    return EvaluationMetrics(
        pronoun_accuracy=pronoun_metrics["accuracy"],
        functionality_accuracy=functionality_metrics["product_type_accuracy"],
        tone_accuracy=tone_metrics["tone_match_rate"],
        response_time=np.mean(response_times) if response_times else 0.0,
        consistency_score=pronoun_metrics["consistency"],
        timestamp=datetime.now().isoformat()
    )

def save_metrics(metrics: EvaluationMetrics, output_file: str):
    """
    Lưu metrics vào file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics.__dict__, f, ensure_ascii=False, indent=2)

def compare_metrics(before_metrics: EvaluationMetrics, after_metrics: EvaluationMetrics) -> Dict:
    """
    So sánh metrics trước và sau khi fine-tuning
    """
    return {
        "pronoun_accuracy_improvement": after_metrics.pronoun_accuracy - before_metrics.pronoun_accuracy,
        "functionality_accuracy_improvement": after_metrics.functionality_accuracy - before_metrics.functionality_accuracy,
        "tone_accuracy_improvement": after_metrics.tone_accuracy - before_metrics.tone_accuracy,
        "response_time_change": after_metrics.response_time - before_metrics.response_time,
        "consistency_improvement": after_metrics.consistency_score - before_metrics.consistency_score
    } 