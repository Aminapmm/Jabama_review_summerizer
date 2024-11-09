from hazm import *
import pandas as pd
import os
#import tiktoken
import numpy as np
from typing import Any
import pandas as pd
#from dotenv import load_dotenv
from string import ascii_lowercase
from langchain.prompts import PromptTemplate
from langchain_mistralai import ChatMistralAI
from langchain.docstore.document import Document
from langchain.chains import LLMChain, StuffDocumentsChain
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
#load_dotenv()

MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
llm = ChatMistralAI(model="mistral-large-latest",temperature=0)

def small_reviews_summary(cust_reviews: str) -> str:
    summary_statement = """فرض کن تو یک نویسنده و تحلیلگر حرفه ای و با تجربه هستی و میخوای نظرات مربوط به یک اقامتگاه  را خلاصه کنی به طوری که نقات ضعف و قوت آن را برای افراد دیگر بیان کنی، حال میخوام که این کار را برای این متن انجام بدی.
                        {cust_reviews}"""
    

    summary_prompt = PromptTemplate(input_variables = ["cust_reviews"], template=summary_statement)
    llm_chain = LLMChain(llm=llm, prompt=summary_prompt)
    review_summary = llm_chain.invoke(cust_reviews)
    return review_summary

# split large reviews
def document_split(cust_reviews: str, chunk_size: int, chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", " ", ""])
    
    # converting string into a document object
    docs = [Document(page_content = t) for t in cust_reviews.split('\n')]
    split_docs = text_splitter.split_documents(docs)
    return split_docs

def map_reduce_summary(split_docs: Any) -> str: 
    map_template = """بر اساس اسناد زیر  که دارای نظرات مربوط به یک اقامتگاه می‌باشد خلاصه ای مفید و ساده برای آن ها ارائه کن.
{docs}
"""

    map_prompt = PromptTemplate.from_template(map_template)
    map_chain = LLMChain(llm=llm, prompt=map_prompt)

    # Reduce
    reduce_template = """برای متنی که در زیر هست که خلاصه نظرات یک اقامتگاه است، همه را جمع آوری کن و خلاصه ای از اطلاعات موجود در هرکدام ارائه کن.
{doc_summaries}"""
    reduce_prompt = PromptTemplate.from_template(reduce_template)

    # Run chain
    reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
# Takes a list of documents, combines them into a single string, and passes this to an LLMChain
    combine_documents_chain = StuffDocumentsChain(llm_chain=reduce_chain, document_variable_name="doc_summaries")

    # Combines and iteratively reduces the mapped documents
    reduce_documents_chain = ReduceDocumentsChain(
        # This is a final chain that is called.
        combine_documents_chain=combine_documents_chain,
        # If documents exceed context for `StuffDocumentsChain`
        collapse_documents_chain=combine_documents_chain,
        # The maximum number of tokens to group documents into.
        token_max=3500,
    )

    # Combining documents by mapping a chain over them, then combining results
    map_reduce_chain = MapReduceDocumentsChain(
        # Map chain
        llm_chain=map_chain,
        # Reduce chain
        reduce_documents_chain=reduce_documents_chain,
        # The variable name in the llm_chain to put the documents in
        document_variable_name="docs",
        # Return the results of the map steps in the output
        return_intermediate_steps=False,
    )
    
    # generating review summary for map reduce method
    cust_review_summary_mr = map_reduce_chain.invoke(split_docs)

    return cust_review_summary_mr


def refine_method_summary(split_docs) -> str:
    prompt_template = """
بر اساس اسناد زیر  که دارای نظرات مربوط به یک اقامتگاه می‌باشد خلاصه ای مفید و ساده به صورت حرفه ای بنویس.
{text}

                  """

    question_prompt = PromptTemplate(
        template=prompt_template, input_variables=["text"]
    )

    refine_prompt_template = """
                یک خلاصه مختصر و مفید که نکات مهم را پوشش دهد برای متن مقابل بنویس:
                {text}
                """

    refine_prompt = PromptTemplate(
        template=refine_prompt_template, input_variables=["text"])

    # Load refine chain
    chain = load_summarize_chain(
        llm=llm,
        chain_type="refine",
        question_prompt=question_prompt,
        refine_prompt=refine_prompt,
        return_intermediate_steps=False,
        input_key="input_text",
    output_key="output_text",
    )
    
    # generating review summary using the refine method
    cust_review_summary_refine = chain.invoke({"input_text": split_docs}, return_only_outputs=True)
    return cust_review_summary_refine

def get_review_summary(reviews:str):


    total_tokens = len(WordTokenizer().tokenize(reviews))
    
    if total_tokens <= 3500:
        cust_review_summary = small_reviews_summary(reviews)
        cust_review_summary_map = "N.A."
        cust_review_summary_refine = "N.A."
    else:
        split_docs = document_split(reviews, 2000, 50)
        #cust_review_summary_map = map_reduce_summary(split_docs)
        cust_review_summary_refine = refine_method_summary(split_docs)
        cust_review_summary = "N.A."
    
    return cust_review_summary['text']