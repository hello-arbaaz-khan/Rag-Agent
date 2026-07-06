from groq import Groq
from decouple import config
from rag.models import DocumemtsChunks,UploadedDocument
from rag.utils.vector_store import search_similar_chunks

client = Groq(
    api_key=config('GROQ_API_KEY')
)

def build_context(chunks):

    context_parts = []

    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1} - Page {chunk['page_number']}]:\n"
            f"{chunk['text']}"
        )            
    
    context = "\n\n".join(context_parts)
    return context


def build_prompt(question, context):
    prompt = f"""Answer based ONLY on context below. Be brief.

Context:
{context}

Question: {question}
Answer:"""
    return prompt


def generate_answer(prompt):
    """
    Get answer from Grow API
    """
    try:
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