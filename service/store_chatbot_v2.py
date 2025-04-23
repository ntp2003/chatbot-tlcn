from typing import Optional
import agents.phone.collect_and_retrieval as phone_collect_and_retrieval
import agents.phone.generate_response as phone_generate_response
import agents.undetermined.generate_response as undetermined_generate_response
import agents.detect_demand as detect_demand

from uuid import UUID
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from models.user_memory import CreateUserMemoryModel, UpdateUserMemoryModel
from repositories.redis import set_value
from repositories.user_memory import (
    get_by_thread_id,
    create as create_user_memory,
    update as update_user_memory,
)


def gen_answer(
    user_id: UUID,
    thread_id: UUID,
    history: list[ChatCompletionMessageParam],
    limit: int = 10,
) -> str:
    conversation_messages = history[-limit:] if len(history) > limit else history
    user_memory = get_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    detect_demand_memory = detect_demand.AgentTemporaryMemory(
        user_memory=user_memory,
    )

    detect_demand_agent = detect_demand.Agent(
        temporary_memory=detect_demand_memory,
    )

    detect_demand_response = detect_demand_agent.run(messages=conversation_messages)

    print(
        "Detect demand response:",
        detect_demand_response,
        (
            detect_demand_memory.user_memory.intent
            if detect_demand_memory.user_memory
            else None
        ),
    )

    if detect_demand_response.type == "message":
        return detect_demand_response.content or ""

    if (
        detect_demand_agent.temporary_memory.user_memory
        and detect_demand_agent.temporary_memory.user_memory.intent.product_type
        == "mobile phone"
    ):
        phone_collect_and_retrieval_memory = (
            phone_collect_and_retrieval.AgentTemporaryMemory(
                user_memory=detect_demand_agent.temporary_memory.user_memory,
            )
        )

        phone_collect_and_retrieval_agent = phone_collect_and_retrieval.Agent(
            temporary_memory=phone_collect_and_retrieval_memory
        )

        phone_collect_and_retrieval_response = phone_collect_and_retrieval_agent.run(
            messages=conversation_messages
        )
        print(
            "Phone collect and retrieval response:",
            phone_collect_and_retrieval_response,
        )
        update_user_memory(
            id=user_memory.id,
            data=UpdateUserMemoryModel.model_validate(
                user_memory, from_attributes=True
            ),
        )
        set_value(
            f"offset:{user_memory.thread_id}", phone_collect_and_retrieval_memory.offset
        )

        phone_generate_response_memory = phone_generate_response.AgentTemporaryMemory(
            user_memory=user_memory
        )
        phone_generate_response_agent = phone_generate_response.Agent(
            temporary_memory=phone_generate_response_memory
        )
        phone_generate_response_response = phone_generate_response_agent.run(
            conversation_messages=conversation_messages,
            instructions=phone_collect_and_retrieval_response.instructions,
            phone_knowledge=phone_collect_and_retrieval_response.knowledge,
        )
        print("Phone generate response:", phone_generate_response_response)
        return phone_generate_response_response.content or "Not content produced"

    undetermined_generate_response_memory = (
        undetermined_generate_response.AgentTemporaryMemory(user_memory=user_memory)
    )
    undetermined_generate_response_agent = undetermined_generate_response.Agent(
        temporary_memory=undetermined_generate_response_memory
    )
    undetermined_generate_response_response = undetermined_generate_response_agent.run(
        conversation_messages=conversation_messages,
    )
    print("Undetermined generate response:", undetermined_generate_response_response)

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )

    return undetermined_generate_response_response.content or "Not content produced"
