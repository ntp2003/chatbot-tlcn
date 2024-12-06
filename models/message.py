from pydantic import ConfigDict, BaseModel
import chainlit as cl


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    author: str
    metadata: dict = {}

    def to_chainlit_message(self) -> cl.Message:
        return cl.Message(
            content=self.content, author=self.author, metadata=self.metadata
        )
