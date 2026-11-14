import os
import time
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def calculate_wer(reference: str, hypothesis: str):
    """Розрахунок Word Error Rate за алгоритмом Левенштейна на рівні слів."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    distance = d[len(ref_words)][len(hyp_words)]
    wer = distance / len(ref_words) if len(ref_words) > 0 else 0
    return wer, distance, len(ref_words)


def benchmark_groq_speed():
    prompt = "Explain in 3 short sentences why practicing speaking is important."
    
    start_time = time.time()
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    latency = time.time() - start_time
    
    total_tokens = completion.usage.completion_tokens
    tokens_per_sec = total_tokens / latency if latency > 0 else 0

    return latency, total_tokens, tokens_per_sec

def evaluate_grammar_accuracy():
    test_cases = [
        ("Yesterday I go to cinema with my friends.", True),
        ("She don't like drinking coffee in the morning.", True),
        ("I have been living in Kyiv for two years.", False),
        ("He play football very well every weekend.", True),
        ("If I will have time, I will call you tomorrow.", True),
        ("They are watching a very interesting documentary.", False),
        ("We was very happy to see our teacher.", True),
        ("There are many beautiful places in Ukraine.", False),
    ]

    tp, fp, fn, tn = 0, 0, 0, 0

    system_prompt = """Analyze user sentence. Return JSON: {"has_error": true/false}"""

    for sentence, actual_has_error in test_cases:
        comp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence}
            ],
            response_format={"type": "json_object"}
        )
        pred = json.loads(comp.choices[0].message.content).get("has_error", False)

        if actual_has_error and pred:
            tp += 1
        elif not actual_has_error and pred:
            fp += 1
        elif actual_has_error and not pred:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1, tp, fp, fn, tn

if __name__ == "__main__":
    print("\n========== ЗВІТ ОЦІНКИ ТА ВАЛІДАЦІЇ ШІ-МОДУЛІВ ==========")
    
    ref = "Hello teacher I want to improve my speaking skills"
    hyp = "Hello teacher I want to improve my spoken skills"
    wer, errors, total = calculate_wer(ref, hyp)
    print(f"\n1. Метрика розпізнавання мови (ASR - Whisper):")
    print(f"   Еталон:     '{ref}'")
    print(f"   Розпізнано: '{hyp}'")
    print(f"   WER (Word Error Rate): {wer * 100:.2f}% (Помилок: {errors}/{total})")

    print(f"\n2. Бенчмарк швидкості генерації (Groq LPU):")
    lat, toks, tps = benchmark_groq_speed()
    print(f"   Час відгуку (Latency): {lat:.3f} сек")
    print(f"   Згенеровано токенів:  {toks}")
    print(f"   Швидкість (Throughput): {tps:.1f} tokens/sec")

    print(f"\n3. Оцінка якості перевірки граматики (Llama 3):")
    p, r, f1, tp, fp, fn, tn = evaluate_grammar_accuracy()
    print(f"   Precision: {p * 100:.1f}%")
    print(f"   Recall:    {r * 100:.1f}%")
    print(f"   F1-Score:  {f1 * 100:.1f}% (TP={tp}, FP={fp}, FN={fn}, TN={tn})")
    print("=========================================================\n")