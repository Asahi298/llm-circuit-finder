#!/usr/bin/env python3
"""
Comprehensive RYS evaluation probe.

Pulls questions from cached HuggingFace datasets (BBH, GSM8K) plus
our custom EQ scenarios. All questions produce short outputs and are
objectively scorable without a judge model.

Usage:
    python comprehensive_probe.py --port 8089 --output results_base.json
    python comprehensive_probe.py --port 8089 --output results_rys.json
    python comprehensive_probe.py --compare results_base.json results_rys.json
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from datasets import load_dataset

from eq_probe import EQ_SCENARIOS, build_eq_prompt, parse_eq_response, score_eq_response


REQUEST_TIMEOUT = 120


def query_model(prompt: str, port: int, max_tokens: int = 512) -> str | None:
    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    payload = {
        "model": "test",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    try:
        r = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except (requests.ConnectionError, requests.Timeout) as e:
        print(f"  [WARN] {e}", file=sys.stderr)
    return None


# ─── Dataset loaders ───────────────────────────────────────────────

def load_gsm8k_questions(limit=50):
    ds = load_dataset("openai/gsm8k", "main")
    test = ds["test"]
    total = len(test)
    step = max(1, total // limit)
    indices = list(range(total - 1, -1, -step))[:limit]
    indices.reverse()

    questions = []
    for idx in indices:
        item = test[idx]
        answer_match = re.search(r'####\s*(-?[\d,]+)', item["answer"])
        if answer_match:
            answer = answer_match.group(1).replace(",", "")
            questions.append({
                "prompt": item["question"] + "\n\nSolve step by step. End with 'The answer is [NUMBER]'.",
                "answer": answer,
                "type": "gsm8k",
            })
    return questions


def load_bbh_questions(subtask, limit=50):
    ds = load_dataset("SaylorTwift/bbh", subtask)
    test = ds["test"]
    total = len(test)
    step = max(1, total // limit)
    indices = list(range(0, total, step))[:limit]

    questions = []
    for idx in indices:
        item = test[idx]
        answer_match = re.search(r'the answer is (.+?)\.?\s*$', item["target"], re.IGNORECASE)
        if answer_match:
            answer = answer_match.group(1).strip()
        else:
            answer = item["target"].strip().split()[-1].rstrip(".")

        questions.append({
            "prompt": item["input"] + "\n\nThink step by step, then give your final answer.",
            "answer": answer,
            "type": f"bbh_{subtask}",
        })
    return questions


def load_eq_questions():
    questions = []
    for scenario in EQ_SCENARIOS:
        questions.append({
            "prompt": build_eq_prompt(scenario),
            "answer": scenario["reference"],
            "emotions": scenario["emotions"],
            "type": "eq",
            "id": scenario["id"],
        })
    return questions


# ─── Scoring ───────────────────────────────────────────────────────

def extract_final_answer(response: str) -> str:
    match = re.search(r'the answer is\s+(.+?)[\.\!\n]', response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'####\s*(.+)', response)
    if match:
        return match.group(1).strip()
    lines = response.strip().split('\n')
    return lines[-1].strip()


def extract_number(text: str) -> str | None:
    nums = re.findall(r'-?[\d,]+\.?\d*', text)
    if nums:
        return nums[-1].replace(",", "")
    return None


def score_question(question: dict, response: str) -> dict:
    if response is None:
        return {"score": 0.0, "parsed": None, "correct": question["answer"]}

    qtype = question["type"]

    if qtype == "eq":
        predicted = parse_eq_response(response, len(question["answer"]))
        score = score_eq_response(question["answer"], predicted) / 100.0
        return {"score": score, "parsed": predicted, "correct": question["answer"]}

    elif qtype == "gsm8k":
        final = extract_final_answer(response)
        pred_num = extract_number(final)
        correct_num = question["answer"]
        if pred_num is not None and pred_num == correct_num:
            score = 1.0
        elif pred_num is not None:
            try:
                diff = abs(float(pred_num) - float(correct_num))
                max_val = max(abs(float(correct_num)), 1)
                score = max(0, 1.0 - diff / max_val) * 0.5
            except ValueError:
                score = 0.0
        else:
            score = 0.0
        return {"score": score, "parsed": pred_num, "correct": correct_num}

    else:  # BBH
        final = extract_final_answer(response)
        correct = question["answer"].strip().lower()
        final_clean = final.strip().lower()
        final_clean = re.sub(r'[^a-z0-9\s\(\)]', '', final_clean).strip()
        correct_clean = re.sub(r'[^a-z0-9\s\(\)]', '', correct).strip()

        if correct_clean in final_clean or final_clean == correct_clean:
            score = 1.0
        elif correct_clean in ("yes", "no"):
            if correct_clean in final_clean.split():
                score = 1.0
            else:
                score = 0.0
        else:
            score = 0.0
        return {"score": score, "parsed": final, "correct": question["answer"]}


# ─── Main evaluation ───────────────────────────────────────────────

def run_full_evaluation(port: int, gsm8k_limit: int = 50, bbh_limit: int = 50) -> dict:
    print("Loading questions...")
    all_questions = []

    try:
        gsm = load_gsm8k_questions(limit=gsm8k_limit)
        all_questions.extend(gsm)
        print(f"  GSM8K: {len(gsm)} questions")
    except Exception as e:
        print(f"  GSM8K: FAILED ({e})")

    for subtask in ["causal_judgement", "date_understanding",
                     "logical_deduction_five_objects", "navigate",
                     "boolean_expressions", "tracking_shuffled_objects_three_objects"]:
        try:
            bbh = load_bbh_questions(subtask, limit=bbh_limit)
            all_questions.extend(bbh)
            print(f"  BBH {subtask}: {len(bbh)} questions")
        except Exception as e:
            print(f"  BBH {subtask}: FAILED ({e})")

    eq = load_eq_questions()
    all_questions.extend(eq)
    print(f"  EQ: {len(eq)} scenarios")

    total = len(all_questions)
    print(f"\nTotal: {total} questions")
    print("Running evaluation...\n")

    results_by_type = {}
    start_time = time.time()

    for i, q in enumerate(all_questions):
        qtype = q["type"]
        if qtype not in results_by_type:
            results_by_type[qtype] = {"scores": [], "total": 0, "correct": 0}

        response = query_model(q["prompt"], port,
                              max_tokens=512 if qtype == "gsm8k" else 256)
        result = score_question(q, response)

        results_by_type[qtype]["scores"].append(result["score"])
        results_by_type[qtype]["total"] += 1
        if result["score"] >= 0.99:
            results_by_type[qtype]["correct"] += 1

        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (total - i - 1) / rate if rate > 0 else 0
        print(f"\r  [{i+1}/{total}] {qtype:40s} "
              f"score={result['score']:.2f}  "
              f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)", end="", flush=True)

    print("\n")
    elapsed_total = time.time() - start_time

    print("=" * 70)
    print(f"{'Probe':40s} {'Accuracy':>8} {'Avg Score':>10} {'N':>5}")
    print("-" * 70)

    overall_scores = []
    summary = {}

    for qtype in sorted(results_by_type.keys()):
        data = results_by_type[qtype]
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        acc = data["correct"] / data["total"] if data["total"] > 0 else 0
        print(f"  {qtype:38s} {acc:>8.1%} {avg:>10.4f} {data['total']:>5}")
        overall_scores.extend(data["scores"])
        summary[qtype] = {"accuracy": acc, "avg_score": avg, "n": data["total"]}

    overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    print("-" * 70)
    print(f"  {'OVERALL':38s} {'':>8} {overall_avg:>10.4f} {len(overall_scores):>5}")
    print(f"\nCompleted in {elapsed_total:.0f}s")
    print("=" * 70)

    return {
        "summary": summary,
        "overall": overall_avg,
        "elapsed": elapsed_total,
        "n_questions": len(overall_scores),
    }


def compare_results(file1: str, file2: str):
    with open(file1) as f:
        r1 = json.load(f)
    with open(file2) as f:
        r2 = json.load(f)

    print(f"\n{'Probe':40s} {'Base':>8} {'RYS':>8} {'Delta':>8}")
    print("-" * 70)

    for qtype in sorted(set(list(r1["summary"].keys()) + list(r2["summary"].keys()))):
        s1 = r1["summary"].get(qtype, {}).get("avg_score", 0)
        s2 = r2["summary"].get(qtype, {}).get("avg_score", 0)
        delta = s2 - s1
        print(f"  {qtype:38s} {s1:>8.4f} {s2:>8.4f} {delta:>+8.4f}")

    print("-" * 70)
    delta_overall = r2["overall"] - r1["overall"]
    print(f"  {'OVERALL':38s} {r1['overall']:>8.4f} {r2['overall']:>8.4f} {delta_overall:>+8.4f}")


def main():
    parser = argparse.ArgumentParser(description="Comprehensive RYS evaluation")
    parser.add_argument("--port", type=int, default=8089)
    parser.add_argument("--gsm8k-limit", type=int, default=50)
    parser.add_argument("--bbh-limit", type=int, default=50)
    parser.add_argument("--output", type=str, default=None,
                        help="Save results to JSON file")
    parser.add_argument("--compare", nargs=2, metavar=("BASE", "RYS"),
                        help="Compare two result files")
    args = parser.parse_args()

    if args.compare:
        compare_results(args.compare[0], args.compare[1])
        return

    results = run_full_evaluation(args.port, args.gsm8k_limit, args.bbh_limit)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
