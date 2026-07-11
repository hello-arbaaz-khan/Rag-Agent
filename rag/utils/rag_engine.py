from decouple import config

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = config('GROQ_API_KEY', default=None)
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing or empty. Please set it in your environment or .env file.")
        from groq import Groq
        _client = Groq(api_key=api_key)
    return _client


def build_context(chunks):

    context_parts = []

    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} - Page {chunk['page_number']}]:\n"
            f"{chunk['text']}"
        )            
    
    context = "\n\n".join(context_parts)
    return context


def build_history_block(history):
    """
    Turn a list of {"question": ..., "answer": ...} dicts (oldest first)
    into a readable conversation transcript for the prompt.
    Returns "" if there's no prior history.
    """
    if not history:
        return ""
 
    turns = []
    for turn in history:
        turns.append(f"User: {turn['question']}\nAssistant: {turn['answer']}")
 
    return "\n\n".join(turns)


def build_prompt(question, context, history=None):
    history_block = build_history_block(history)
 
    history_section = (
        f"Conversation so far:\n{history_block}\n\n"
        if history_block
        else ""
    )
 
    prompt = f"""Answer based ONLY on the document context below. Be brief.
Use the conversation history only to resolve references (e.g. "it", "that", "my first question") - the document context is still the source of truth for facts.
 
{history_section}Context:
{context}
 
Question: {question}
Answer:"""
    return prompt
 
 
def generate_answer(prompt):
    """
    Get answer from Grow API
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )
 
        answer = response.choices[0].message.content
        return answer.strip()
 
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise ValueError(f"Groq API error: {str(e)}")


def generate_answer(prompt):
    """
    Get answer from Grow API
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )

        answer = response.choices[0].message.content
        return answer.strip()

    except ValueError as ve:
        raise ve
    except Exception as e:
        raise ValueError(f"Groq API error: {str(e)}")


def calculate_confidence(similar_chunks):
    """ calculate confidence based on similarity scores """
    if not similar_chunks:
        return 0.0

    similarities = [
        chunk['similarity']
        for chunk in similar_chunks
    ]
    average_similarity = sum(similarities) / len(similarities)
    return round(average_similarity, 2)