# Fine-tuning GPT for Vietnamese Pronouns using LoRA

This project provides code to fine-tune a large language model (like GPT-4) for better handling of Vietnamese pronouns and honorifics using LoRA (Low-Rank Adaptation).

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Data Preparation

1. The `prepare_data.py` script helps create training data in the required format. You can:
   - Use the example conversations provided
   - Add your own conversations to the list
   - Create a custom JSON file following the same format

The data format should be:
```json
{
    "context": "Situation description",
    "speaker_role": "Role of speaker",
    "listener_role": "Role of listener",
    "response": "Response with appropriate pronouns"
}
```

2. Run the data preparation script:
```bash
python prepare_data.py
```

## Training

1. The `train_lora.py` script handles the fine-tuning process using LoRA. Key features:
   - Uses 4-bit quantization for efficient training
   - Implements LoRA for parameter-efficient fine-tuning
   - Supports customizable training parameters

2. Run the training:
```bash
python train_lora.py
```

## Configuration

You can modify these parameters in `train_lora.py`:
- `model_name`: Base model to fine-tune
- `num_train_epochs`: Number of training epochs
- `learning_rate`: Learning rate for training
- `per_device_train_batch_size`: Batch size per GPU
- LoRA parameters (rank, alpha, target modules)

## Output

The fine-tuned model will be saved in the `vietnamese_pronouns_model` directory. This includes:
- LoRA weights
- Training configuration
- Tokenizer files

## Notes

- Make sure you have sufficient GPU memory for training
- The default configuration uses 4-bit quantization to reduce memory usage
- Adjust batch size and gradient accumulation steps based on your GPU memory
- Consider using a validation set for better monitoring of training progress 