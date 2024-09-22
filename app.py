import gradio as gr
import alembic.config
from service.openai import gen_answer

alembic.config.main(argv=["--raiseerr", "upgrade", "head"])

gr.ChatInterface(
    gen_answer,
    chatbot=gr.Chatbot(height=300),
    textbox=gr.Textbox(placeholder="You can ask me anything", container=False, scale=7),
    title="OpenAI Chat Bot",
    retry_btn=None,
    undo_btn="Delete Previous",
    clear_btn="Clear",
).launch()

gr.ChatInterface(gen_answer).launch()
