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
    conversation_messages = history[-limit:] if len(history) > limit else history # lấy 10 message cuối
    user_memory = get_by_thread_id(thread_id) # get user memory theo thread_id
    if user_memory is None:
        user_memory = create_user_memory(
            CreateUserMemoryModel(user_id=user_id, thread_id=thread_id)
        )
    # create temporary memory for demand detection
    detect_demand_memory = detect_demand.AgentTemporaryMemory(
        user_memory=user_memory,
    )

    detect_demand_agent = detect_demand.Agent(
        temporary_memory=detect_demand_memory,
    )

    detect_demand_response = detect_demand_agent.run(messages=conversation_messages) # initializes and runs the demand detection agent , analyze user messages to understand their intent

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

def gen_answer_for_messenger(
    user_id: UUID,
    thread_id: UUID,
    messages: list[ChatCompletionMessageParam],
) -> str:
    try:
        # Convert messages to proper format and limit history
        conversation_messages = messages[-10:] if len(messages) > 10 else messages
        
        # Extract gender from the latest user message
        user_gender = "unknown"
        for msg in reversed(conversation_messages):
            if msg.get("role") == "user" and "gender" in msg:
                user_gender = msg.get("gender")
                break
        
        # Get or create user memory
        user_memory = get_by_thread_id(thread_id)
        if user_memory is None:
            user_memory = create_user_memory(
                CreateUserMemoryModel(
                    user_id=user_id,
                    thread_id=thread_id,
                    gender=user_gender  # Add gender to user memory
                )
            )
        else:
            # Update gender in existing memory if needed
            if not hasattr(user_memory, 'gender') or user_memory.gender != user_gender:
                user_memory.gender = user_gender

        # Initialize demand detection with gender context
        detect_demand_memory = detect_demand.AgentTemporaryMemory(
            user_memory=user_memory,
        )
        detect_demand_agent = detect_demand.Agent(
            temporary_memory=detect_demand_memory,
        )

        # Add gender context to messages before processing
        messages_with_context = []
        for msg in conversation_messages:
            if msg.get("role") == "user":
                # Add gender context to user messages
                content = msg.get("content", "")
                if user_gender != "unknown":
                    # Add gender context as system message before user message
                    messages_with_context.append({
                        "role": "system",
                        "content": f"User gender: {user_gender}. Please use appropriate pronouns and honorifics."
                    })
            messages_with_context.append(msg)

        detect_demand_response = detect_demand_agent.run(messages=messages_with_context)

        print(
            "Detect demand response:",
            detect_demand_response,
            (
                detect_demand_memory.user_memory.intent
                if detect_demand_memory.user_memory
                else None
            ),
        )

        # Handle direct message response from demand detection
        if detect_demand_response.type == "message":
            return detect_demand_response.content or "Xin lỗi, tôi không hiểu yêu cầu của bạn"

        # Handle mobile phone related queries
        if (
            detect_demand_agent.temporary_memory.user_memory
            and detect_demand_agent.temporary_memory.user_memory.intent.product_type
            == "mobile phone"
        ):
            # Initialize phone collection agent with gender context
            phone_collect_memory = phone_collect_and_retrieval.AgentTemporaryMemory(
                user_memory=detect_demand_agent.temporary_memory.user_memory,
            )
            phone_collect_agent = phone_collect_and_retrieval.Agent(
                temporary_memory=phone_collect_memory
            )
            
            # Get phone information
            phone_collect_response = phone_collect_agent.run(
                messages=messages_with_context  # Pass messages with gender context
            )
            print("Phone collect response:", phone_collect_response)
            
            # Update user memory and offset
            update_user_memory(
                id=user_memory.id,
                data=UpdateUserMemoryModel.model_validate(
                    user_memory, from_attributes=True
                ),
            )
            set_value(
                f"offset:{user_memory.thread_id}", phone_collect_memory.offset
            )

            # Generate response for phone query with gender context
            phone_response_memory = phone_generate_response.AgentTemporaryMemory(
                user_memory=user_memory
            )
            phone_response_agent = phone_generate_response.Agent(
                temporary_memory=phone_response_memory
            )
            phone_response = phone_response_agent.run(
                conversation_messages=messages_with_context,  # Pass messages with gender context
                instructions=phone_collect_response.instructions,
                phone_knowledge=phone_collect_response.knowledge,
            )
            print("Phone response:", phone_response)
            return phone_response.content or "Xin lỗi, tôi không thể tìm thấy thông tin điện thoại phù hợp"

        # Handle undetermined queries
        undetermined_memory = undetermined_generate_response.AgentTemporaryMemory(
            user_memory=user_memory
        )
        undetermined_agent = undetermined_generate_response.Agent(
            temporary_memory=undetermined_memory
        )
        undetermined_response = undetermined_agent.run(
            conversation_messages=messages_with_context,  # Pass messages with gender context
        )
        print("Undetermined response:", undetermined_response)

        # Update final user memory state
        update_user_memory(
            id=user_memory.id,
            data=UpdateUserMemoryModel.model_validate(
                user_memory, from_attributes=True
            ),
        )

        return undetermined_response.content or "Xin lỗi, tôi không hiểu yêu cầu của bạn"

    except Exception as e:
        print(f"Error in gen_answer_for_messenger: {str(e)}")
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