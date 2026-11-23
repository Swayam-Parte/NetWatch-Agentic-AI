"""Retrieves similar historical examples using TF-IDF + cosine similarity."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CASES = [
 {"case_id":"CASE001","problem":"Internet not working and router is offline","resolution":"Check router power and cables; restart and wait 60 seconds."},
 {"case_id":"CASE002","problem":"Router online but internet not working","resolution":"Check WAN cable, WAN indicator and another device."},
 {"case_id":"CASE003","problem":"Internet unavailable during area outage","resolution":"Inform customer about the outage and escalate to network support."},
 {"case_id":"CASE004","problem":"Internet not working after router restart","resolution":"Check WAN connection and perform service-side diagnostics."},
 {"case_id":"CASE005","problem":"WAN light normal but internet unavailable on multiple devices","resolution":"Perform service-side diagnostics and escalate if unresolved."},
]
_VECTOR = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
_MATRIX = _VECTOR.fit_transform([c['problem'] for c in CASES])
def find_similar_cases(problem: str, top_k=2, threshold=0.08):
    scores = cosine_similarity(_VECTOR.transform([problem]), _MATRIX).flatten()
    ranked = scores.argsort()[::-1][:top_k]
    return [{**CASES[i], 'similarity': round(float(scores[i]),3)} for i in ranked if scores[i] >= threshold]
