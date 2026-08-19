# from apps.rag.models import UploadedDocument, DriveDocument

# doc_ids = [23, 9, 3, 22, 21, 5]

# print("Total UploadedDocument rows:", UploadedDocument.objects.count())
# print("Total DriveDocument rows:", DriveDocument.objects.count())
# print()

# for did in doc_ids:
#     try:
#         u = UploadedDocument.objects.get(id=did)
#     except UploadedDocument.DoesNotExist:
#         print(f"id={did} -> UploadedDocument NOT FOUND")
#         continue
#     dd = DriveDocument.objects.filter(document_id=did).first()
#     print(f"id={did} | name={u.name!r} | has DriveDocument: {dd is not None} | drive_sync_status: {dd.sync_status if dd else 'N/A'}")

# print()
# print("---- All DriveDocument rows ----")
# for dd in DriveDocument.objects.all():
#     print(f"drive_id={dd.id} | name={dd.name!r} | document_id={dd.document_id} | sync_status={dd.sync_status}")

# from apps.rag.utils.query_intent import parse_query_intent
# from apps.rag.services.search_service import _matches_date_filter, MIN_RELEVANCE
# from apps.rag.models import DriveDocument

# query = "give me documents that info about geopolitical"

# intent = parse_query_intent(query)
# print("Parsed intent:", intent)
# print("topic:", repr(intent.get("topic")))
# print("date_filter:", intent.get("date_filter"))
# print()

# all_docs = list(DriveDocument.objects.all())
# print(f"Total DriveDocument rows before date filter: {len(all_docs)}")

# date_filter = intent.get("date_filter") or {}
# if date_filter.get("type"):
#     filtered = [d for d in all_docs if _matches_date_filter(d.drive_modified_at, date_filter)]
#     print(f"Total DriveDocument rows AFTER date filter ({date_filter}): {len(filtered)}")
# else:
#     print("No date_filter type set, so no date filtering happened.")

from apps.rag.utils.query_intent import parse_query_intent
from apps.rag.utils.vector_store import search_all_documents
from apps.rag.services.search_service import score_filename_match, MIN_RELEVANCE
from apps.rag.models import DriveDocument
from django.db.models import Count

query = "give me documents that info about geopolitical"

intent = parse_query_intent(query)
topic = intent["topic"]
date_filter = intent["date_filter"]
print("topic:", repr(topic))
print("date_filter:", date_filter)
print()

all_docs = list(
    DriveDocument.objects.select_related("document")
    .annotate(annotated_chunks=Count("document__chunks"))
    .all()
)
print(f"all_docs count: {len(all_docs)}")

content_matches = search_all_documents(topic, top_k=1000)
content_scores = {m["document_id"]: m["relevance_score"] for m in content_matches}
print(f"content_matches count: {len(content_matches)}")
print("content_scores:", content_scores)
print()

print(f"MIN_RELEVANCE = {MIN_RELEVANCE}")
print()
print("---- per-doc breakdown ----")
kept = 0
for doc in all_docs:
    name_score = score_filename_match(doc.name, topic)
    content_score = content_scores.get(doc.document_id, 0.0) if doc.document_id else 0.0
    final_score = max(name_score, content_score)
    status = "KEPT" if final_score >= MIN_RELEVANCE else "dropped"
    if final_score >= MIN_RELEVANCE:
        kept += 1
    print(f"drive_id={doc.id} name={doc.name!r} document_id={doc.document_id} name_score={name_score} content_score={content_score} final_score={final_score} -> {status}")

print()
print(f"TOTAL KEPT: {kept}")