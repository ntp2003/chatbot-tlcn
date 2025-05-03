from typing import Optional
import agents.phone.collect_and_retrieval as phone_collect_and_retrieval
import agents.phone.generate_response as phone_generate_response

import agents.laptop.collect_and_retrieval as laptop_collect_and_retrieval
import agents.laptop.generate_response as laptop_generate_response

import agents.accessory.collect_and_retrieval as accessories_collect_and_retrieval
import agents.accessory.generate_response as accessories_generate_response

import agents.undetermined.generate_response as undetermined_generate_response
import agents.detect_demand as detect_demand
from service.wandb import client as wandb_client
from uuid import UUID
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from models.user_memory import (
    UserMemoryModel,
    ProductType,
    CreateUserMemoryModel,
    UpdateUserMemoryModel,
)
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
    gen_answer_call = wandb_client.create_call(
        op="gen_answer",
        inputs=locals(),
    )
    conversation_messages = history[-limit:] if len(history) > limit else history
    user_memory = get_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    detect_demand_memory = detect_demand.AgentTemporaryMemory(
        user_memory=user_memory,
    )

    detect_demand_call = wandb_client.create_call(
        op="detect_demand",
        inputs={
            "temporary_memory": detect_demand_memory,
            "messages": conversation_messages,
        },
    )
    detect_demand_system_prompt_config = detect_demand.SystemPromptConfig()
    detect_demand_agent = detect_demand.Agent(
        temporary_memory=detect_demand_memory,
        system_prompt_config=detect_demand_system_prompt_config,
    )

    detect_demand_response = detect_demand_agent.run(messages=conversation_messages)
    detect_demand_response = detect_demand_agent.post_process(
        detect_demand_response, user_memory
    )
    print(
        "Detect demand response:",
        detect_demand_response,
        (
            detect_demand_memory.user_memory.intent
            if detect_demand_memory.user_memory
            else None
        ),
    )
    wandb_client.finish_call(detect_demand_call, output=detect_demand_response)
    if detect_demand_response.type == "message":
        return detect_demand_response.content or ""

    detect_demand_agent_temp_memory_user_memory = (
        detect_demand_agent.temporary_memory.user_memory
    )
    product_type = detect_demand_agent_temp_memory_user_memory.intent.product_type  # type: ignore

    match product_type:
        case ProductType.MOBILE_PHONE:
            handler = handle_phone_request
        case ProductType.LAPTOP:
            handler = handle_laptop_request
        case ProductType.ACCESSORY:
            handler = handle_accessories_request
        case _:
            handler = handle_undetermined_request

    response = handler(
        user_memory=detect_demand_agent_temp_memory_user_memory,  # type: ignore
        conversation_messages=conversation_messages,
    )

    wandb_client.finish_call(gen_answer_call, output=response)
    return response


def handle_phone_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:

    # 1. collect and retrieval phone
    collect_and_retrieval_memory = phone_collect_and_retrieval.AgentTemporaryMemory(
        user_memory=user_memory,
    )  # init temporary memory collect and retrieval phone

    collect_and_retrieval_call = wandb_client.create_call(
        op="collect_and_retrieval_phone",
        inputs={
            "temporary_memory": collect_and_retrieval_memory,
            "messages": conversation_messages,
        },
    )  # create call collect and retrieval phone

    collect_and_retrieval_system_prompt_config = (
        phone_collect_and_retrieval.SystemPromptConfig()
    )

    collect_and_retrieval_agent = phone_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory,
        system_prompt_config=collect_and_retrieval_system_prompt_config,
    )  # init agent collect and retrieval phone

    # run agent collect and retrieval phone to get instructions and knowledge
    collect_and_retrieval_response = collect_and_retrieval_agent.run(
        messages=conversation_messages
    )

    print("Phone collect and retrieval response:", collect_and_retrieval_response)

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    set_value(
        f"offset:{user_memory.thread_id}", collect_and_retrieval_memory.offset
    )  # lưu offset vào redis

    wandb_client.finish_call(
        collect_and_retrieval_call,
        output={
            "response": collect_and_retrieval_response,
            "temporary_memory": collect_and_retrieval_memory,
        },
    )

    # 2. generate response phone
    generate_memory = phone_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )

    generate_agent_call = wandb_client.create_call(
        op="generate_response_phone",
        inputs={
            "temporary_memory": generate_memory,
            "conversation_messages": conversation_messages,
            "instructions": collect_and_retrieval_response.instructions,
            "phone_knowledge": collect_and_retrieval_response.knowledge,
        },
    )  # create call generate response phone

    generate_response_system_prompt_config = (
        phone_generate_response.SystemPromptConfig()
    )

    generate_agent = phone_generate_response.Agent(
        temporary_memory=generate_memory,
        system_prompt_config=generate_response_system_prompt_config,
    )  # init agent generate response phone
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
        instructions=collect_and_retrieval_response.instructions,
        phone_knowledge=collect_and_retrieval_response.knowledge,
    )  # run agent generate response about phone
    print("Phone generate response:", generate_response)
    wandb_client.finish_call(
        generate_agent_call,
        output={
            "response": generate_response,
            "temporary_memory": generate_memory,
        },
    )
    return generate_response.content or "Not content produced"


def handle_laptop_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:
    collect_and_retrieval_memory = laptop_collect_and_retrieval.AgentTemporaryMemory(
        user_memory=user_memory,
    )

    collect_and_retrieval_system_prompt_config = (
        laptop_collect_and_retrieval.SystemPromptConfig()
    )

    collect_and_retrieval_agent = laptop_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory,
        system_prompt_config=collect_and_retrieval_system_prompt_config,
    )
    collect_and_retrieval_response = collect_and_retrieval_agent.run(
        messages=conversation_messages
    )

    print(
        "Laptop collect and retrieval response:",
        collect_and_retrieval_response,
    )

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    set_value(f"offset:{user_memory.thread_id}", collect_and_retrieval_memory.offset)

    generate_memory = laptop_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )
    generate_response_system_prompt_config = (
        laptop_generate_response.SystemPromptConfig()
    )
    generate_agent = laptop_generate_response.Agent(
        temporary_memory=generate_memory,
        system_prompt_config=generate_response_system_prompt_config,
    )
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
        instructions=collect_and_retrieval_response.instructions,
        laptop_knowledge=collect_and_retrieval_response.knowledge,
    )  # run agent generate response about laptop
    print("Laptop generate response:", generate_response)
    return generate_response.content or "Not content produced"


def handle_accessories_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:
    collect_and_retrieval_memory = (
        accessories_collect_and_retrieval.AgentTemporaryMemory(
            user_memory=user_memory,
        )
    )
    collect_and_retrieval_system_prompt_config = (
        accessories_collect_and_retrieval.SystemPromptConfig()
    )

    collect_and_retrieval_agent = accessories_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory,
        system_prompt_config=collect_and_retrieval_system_prompt_config,
    )
    collect_and_retrieval_response = collect_and_retrieval_agent.run(
        messages=conversation_messages
    )

    print(
        "Accessories collect and retrieval response:",
        collect_and_retrieval_response,
    )

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    set_value(f"offset:{user_memory.thread_id}", collect_and_retrieval_memory.offset)

    generate_memory = accessories_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )
    generate_response_system_prompt_config = (
        accessories_generate_response.SystemPromptConfig()
    )
    generate_agent = accessories_generate_response.Agent(
        temporary_memory=generate_memory,
        system_prompt_config=generate_response_system_prompt_config,
    )
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
        instructions=collect_and_retrieval_response.instructions,
        accessory_knowledge=collect_and_retrieval_response.knowledge,
    )
    print("Accessories generate response:", generate_response)
    return generate_response.content or "Not content produced"


def handle_undetermined_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:

    generate_agent_call = wandb_client.create_call(
        op="generate_response_undetermined",
        inputs={
            "temporary_memory": user_memory,
            "conversation_messages": conversation_messages,
        },
    )
    generate_memory = undetermined_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )
    generate_response_system_prompt_config = (
        undetermined_generate_response.SystemPromptConfig()
    )
    generate_agent = undetermined_generate_response.Agent(
        temporary_memory=generate_memory,
        system_prompt_config=generate_response_system_prompt_config,
    )
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
    )

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    print("Undetermined generate response:", generate_response)

    wandb_client.finish_call(
        generate_agent_call,
        output={
            "response": generate_response,
            "temporary_memory": generate_memory,
        },
    )
    return generate_response.content or "Not content produced"
