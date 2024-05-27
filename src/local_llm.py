# This file contains code for run local LLM
from src.utils import summary_prompt


# # Example with GPT4All
#
# from gpt4all import GPT4All
#
#
# def summarize_local(input_text: str) -> str:
#     model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf", device="gpu")
#     output = model.generate(summary_prompt(input_text), max_tokens=1024, temp=0.6)
#     return output


# Example with HuggingFace
#
# import os
# from transformers import AutoTokenizer, AutoModelForCausalLM
#
#
# def summarize_local(input_text: str) -> str:
#     # load token for HuggingFace
#     access_token = os.getenv("huggingface_token")
#
#     # load tokenizer and model
#     tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b-it", token=access_token)
#     model = AutoModelForCausalLM.from_pretrained("google/gemma-2b-it", token=access_token)
#
#     # tokenize text
#     input_ids = tokenizer(summary_prompt(input_text), return_tensors="pt")
#
#     # generate answer
#     outputs = model.generate(**input_ids, max_length=1024)
#
#     # return decoded output
#     return tokenizer.decode(outputs[0])
