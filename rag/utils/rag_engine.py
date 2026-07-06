from groq import Groq
from decouple import config
from rag.models import DocumemtsChunks,UploadedDocument
from rag.utils.vector_store import search_similar_chunks

client = Groq(
    api_key=config('GROQ_API_KEY')
)

def build_context(search_similar_chunks):

    context_parts = []

    for i,chunk in enumerate(search_similar_chunks):
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

def get_answer(question,document_id):

    try:
        document = UploadedDocument.objects.get(id=document_id)
    except UploadedDocument.DoesNotExist:
        raise ValueError(f"Document {document_id} doesn't exist")

    similar_chunks = search_similar_chunks(
        question = question,
        document_id = document_id,
        top_k = 3
    )
    if not similar_chunks:
        return {
            "question": question,
            "answer": "Answer Not Found in Document",
            "source_chunks": [],
            "document_name": document.name,
            "confidence_score": 0.0
        }
    
    context = build_context(similar_chunks)
    prompt = build_prompt(question,context)
    answer = generate_answer(prompt)
    confidence = calculate_confidence(similar_chunks)
    
    return {
        "question":        question,
        "answer":          answer,
        "source_chunks":   similar_chunks,
        "document_name":   document.name,
        "confidence_score": confidence
    }