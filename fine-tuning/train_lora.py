import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model,
    TaskType
)
from datasets import load_dataset
import os
import sys
from typing import Dict, Sequence

def load_model_and_tokenizer(model_name: str):
    """Load the base model and tokenizer."""
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    model = prepare_model_for_kbit_training(model)
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer

def create_lora_config():
    """Create LoRA configuration."""
    return LoraConfig(
        r=16,  # Rank
        lora_alpha=32,
        target_modules=["query_key_value"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )

def prepare_dataset(tokenizer, data_path: str, max_length: int = 512):
    """Prepare and tokenize the dataset."""
    dataset = load_dataset("json", data_files=data_path)
    
    def tokenize_function(examples):
        # Combine instruction and output
        texts = [
            f"Instruction: {instruction}\nOutput: {output}"
            for instruction, output in zip(examples["instruction"], examples["output"])
        ]
        
        return tokenizer(
            texts,
            truncation=True,
            max_length=max_length,
            padding="max_length"
        )
    
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names
    )
    
    return tokenized_dataset

def main():
    # Configuration
    model_name = "gpt4all/gpt4all-13b-snoozy"  # or your preferred base model
    data_path = "training_data.jsonl"
    output_dir = "vietnamese_pronouns_model"
    
    print("Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(model_name)
    
    print("Creating LoRA configuration...")
    lora_config = create_lora_config()
    model = get_peft_model(model, lora_config)
    
    print("Preparing dataset...")
    dataset = prepare_dataset(tokenizer, data_path)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="epoch",
        warmup_ratio=0.03,
        weight_decay=0.01,
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
    )
    
    print("Starting training...")
    trainer.train()
    
    # Save the final model
    print("Saving model...")
    trainer.save_model(output_dir)
    
if __name__ == "__main__":
    main() 