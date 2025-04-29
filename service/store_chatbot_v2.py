from typing import Optional
import agents.phone.collect_and_retrieval as phone_collect_and_retrieval
import agents.phone.generate_response as phone_generate_response

import agents.laptop.collect_and_retrieval as laptop_collect_and_retrieval
import agents.laptop.generate_response as laptop_generate_response

import agents.accessory.collect_and_retrieval as accessories_collect_and_retrieval
import agents.accessory.generate_response as accessories_generate_response

import agents.undetermined.generate_response as undetermined_generate_response
import agents.detect_demand as detect_demand

from uuid import UUID
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from models.user_memory import UserMemoryModel, CreateUserMemoryModel, UpdateUserMemoryModel, ProductType
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
) -> str: # generate response for user
    conversation_messages = history[-limit:] if len(history) > limit else history # limit 10 message cuối
    
    user_memory = get_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    # xác định nhu cầu user
    detect_demand_memory = detect_demand.AgentTemporaryMemory(
        user_memory=user_memory,
    ) # init temporary memory detect demand

    detect_demand_agent = detect_demand.Agent(
        temporary_memory=detect_demand_memory,
    ) # init agent detect demand

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

    if detect_demand_response.type == "message":
        return detect_demand_response.content or ""

    detect_demand_agent_temp_memory_user_memory = detect_demand_agent.temporary_memory.user_memory
    product_type = detect_demand_agent_temp_memory_user_memory.get("intent", {}).get("product_type")

    if (
        detect_demand_agent_temp_memory_user_memory
        and product_type == ProductType.MOBILE_PHONE
    ): # user demand is mobile phone
        return handle_phone_request(user_memory, conversation_messages)
    elif (
        detect_demand_agent_temp_memory_user_memory
        and product_type == ProductType.LAPTOP
    ):  # user demand is laptop
        return handle_laptop_request(user_memory, conversation_messages)
    elif (
        detect_demand_agent_temp_memory_user_memory
        and product_type == ProductType.ACCESSORY
    ): # user demand is accessory 
        return handle_accessories_request(user_memory, conversation_messages)
    else: # user demand is undetermined, faqs 
        return handle_undetermined_request(user_memory, conversation_messages)

    
def handle_phone_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:
    
   # 1. collect and retrieval phone
    collect_and_retrieval_memory = phone_collect_and_retrieval.AgentTemporaryMemory(
        user_memory=user_memory,
    )  # init temporary memory collect and retrieval phone

    collect_and_retrieval_agent = phone_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory
    ) #init agent collect and retrieval phone
    
    # run agent collect and retrieval phone to get instructions and knowledge
    collect_and_retrieval_response = collect_and_retrieval_agent.run(messages=conversation_messages) 
    
    print("Phone collect and retrieval response:", collect_and_retrieval_response)
    
    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    set_value(f"offset:{user_memory.thread_id}", collect_and_retrieval_memory.offset) # lưu offset vào redis

    # 2. generate response phone
    generate_memory = phone_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )
    generate_agent = phone_generate_response.Agent(
        temporary_memory=generate_memory
    ) # init agent generate response phone
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
        instructions=collect_and_retrieval_response.instructions,
        phone_knowledge=collect_and_retrieval_response.knowledge,
    ) # run agent generate response about phone
    print("Phone generate response:", generate_response)

    return generate_response.content or "Not content produced"

def handle_laptop_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:
    collect_and_retrieval_memory = laptop_collect_and_retrieval.AgentTemporaryMemory(
        user_memory=user_memory,
    )
    collect_and_retrieval_agent = laptop_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory
    )
    collect_and_retrieval_response = collect_and_retrieval_agent.run(messages=conversation_messages)
    
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
    generate_agent = laptop_generate_response.Agent(
        temporary_memory=generate_memory
    )
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
        instructions=collect_and_retrieval_response.instructions,
        laptop_knowledge=collect_and_retrieval_response.knowledge,
    ) # run agent generate response about laptop
    print("Laptop generate response:", generate_response)
    return generate_response.content or "Not content produced"

def handle_accessories_request(
    user_memory: UserMemoryModel,
    conversation_messages: list[ChatCompletionMessageParam],
) -> str:
    collect_and_retrieval_memory = accessories_collect_and_retrieval.AgentTemporaryMemory(
        user_memory=user_memory,
    )
    collect_and_retrieval_agent = accessories_collect_and_retrieval.Agent(
        temporary_memory=collect_and_retrieval_memory
    )
    collect_and_retrieval_response = collect_and_retrieval_agent.run(messages=conversation_messages)
    
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
    generate_agent = accessories_generate_response.Agent(
        temporary_memory=generate_memory
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
    generate_memory = undetermined_generate_response.AgentTemporaryMemory(
        user_memory=user_memory
    )
    generate_agent = undetermined_generate_response.Agent(
        temporary_memory=generate_memory
    )
    generate_response = generate_agent.run(
        conversation_messages=conversation_messages,
    )

    update_user_memory(
        id=user_memory.id,
        data=UpdateUserMemoryModel.model_validate(user_memory, from_attributes=True),
    )
    print("Undetermined generate response:", generate_response)
    return generate_response.content or "Not content produced"

def gen_answer_for_messenger(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
    limit: int = 10,
) -> str:
    """
    Generate answer for Facebook Messenger users.
    Similar to gen_answer but optimized for Messenger platform with additional context handling.
    """
    # Limit conversation history
    conversation_messages = messages[-limit:] if len(messages) > limit else messages
    
    # Get or create user memory
    user_memory = get_by_thread_id(thread_id)
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )

    # Detect user demand
    detect_demand_memory = detect_demand.AgentTemporaryMemory(
        user_memory=user_memory,
    )
    detect_demand_agent = detect_demand.Agent(
        temporary_memory=detect_demand_memory,
    )
    detect_demand_response = detect_demand_agent.run(messages=conversation_messages)
    
    print(
        "Messenger demand detection:",
        detect_demand_response,
        (
            detect_demand_memory.user_memory.intent
            if detect_demand_memory.user_memory
            else None
        ),
    )

    # Handle direct message response from demand detection
    if detect_demand_response.type == "message":
        return detect_demand_response.content or "Xin lỗi, tôi không hiểu yêu cầu của bạn."

    detect_demand_agent_temp_memory_user_memory = detect_demand_agent.temporary_memory.user_memory
    product_type = detect_demand_agent_temp_memory_user_memory.intent.product_type if detect_demand_agent_temp_memory_user_memory.intent else None

    # Process based on product type
    try:
        if product_type == ProductType.MOBILE_PHONE:
            return handle_phone_request(user_memory, conversation_messages)
        elif product_type == ProductType.LAPTOP:
            return handle_laptop_request(user_memory, conversation_messages)
        elif product_type == ProductType.ACCESSORY:
            return handle_accessories_request(user_memory, conversation_messages)
        else:
            return handle_undetermined_request(user_memory, conversation_messages)
    except Exception as e:
        print(f"Error in messenger response generation: {str(e)}")
        return "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau."

'''
def gen_answer_for_messenger(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
) -> str:
    formatted_messages = []
    formatted_messages.append({"role": "system", "content": role_prompt})
    formatted_messages.append({"role": "system", "content": knowledge_prompt})
    
    for message in messages:
        formatted_messages.append(message)
    
    formatted_messages.append({"role": "system", "content": constraints_prompt})
    formatted_messages.append({"role": "system", "content": workflow_prompt})
    formatted_messages.append({"role": "system", "content": initialization_prompt})

    try:
        response_text,_ = gen_openai_answer(
            user_id=user_id,
            thread_id=thread_id,
            messages=formatted_messages,
            tools=tools,
        )
    except Exception as e:
        response_text = f"Đã xảy ra lỗi: {e}"

    return response_text

'''