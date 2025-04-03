import os
import pandas as pd
from google.cloud import bigquery
from io import BytesIO
from dotenv import load_dotenv
import logging



# LangChain & vector store imports
from langchain_community.document_loaders import DataFrameLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# # Instead of: import openai
# from langfuse.openai import OpenAI
# from langfuse.decorators import observe
# from langfuse import Langfuse
# import asyncio

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chains import ConversationalRetrievalChain

# Load environment variables from .env
load_dotenv()

# Set up logging (optional; adjust format as needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set API keys and tokens from environment variables
os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")
# os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
os.environ["DEEPSEEK_API_KEY"] = os.getenv('DEEPSEEK_API_KEY')
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ['LANGFUSE_PUBLIC_KEY'] = os.getenv("LANGFUSE_PUBLIC_KEY")
os.environ['LANGFUSE_SECRET_KEY'] = os.getenv("LANGFUSE_SECRET_KEY")
os.environ['LANGFUSE_HOST'] = os.getenv("LANGFUSE_HOST")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Set up BigQuery credentials; ensure GOOGLE_APPLICATION_CREDENTIALS points to your file
# For example, if using a file mounted in your container:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# ---------- BigQuery Data Fetching Functions ----------

def fetch_reviews(asin: str) -> pd.DataFrame:
    """
    Fetches product review data for a given ASIN from BigQuery.
    Adjust the query and table names to match your BigQuery dataset.
    """
    client = bigquery.Client()
    query = f"""
    SELECT *
    FROM `spheric-engine-451615-a8.Amazon_Reviews_original_dataset_v3.Amazon_dataset_V3`
    WHERE parent_asin = '{asin}'
    """
    try:
        review_df = client.query(query).to_dataframe()
        logger.info(f"Fetched {len(review_df)} review records for ASIN: {asin}")
    except Exception as e:
        logger.exception(f"Error fetching reviews for ASIN {asin}: {e}")
        review_df = pd.DataFrame()
    return review_df

def fetch_metadata(asin: str) -> pd.DataFrame:
    """
    Fetches product metadata for a given ASIN from BigQuery.
    Adjust the query and table names as necessary.
    """
    client = bigquery.Client()
    query = f"""
    SELECT *
    FROM `spheric-engine-451615-a8.Amazon_Reviews_original_dataset_v4.meta_data`
    WHERE parent_asin = '{asin}'
    """
    try:
        meta_df = client.query(query).to_dataframe()
        logger.info(f"Fetched {len(meta_df)} metadata records for ASIN: {asin}")
    except Exception as e:
        logger.exception(f"Error fetching metadata for ASIN {asin}: {e}")
        meta_df = pd.DataFrame()
    return meta_df
# def handle_user_input(user_input):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(async_handle_user_input(user_input))

# async def async_handle_user_input(user_input):
#     answer = await qa_chain.ainvoke(user_input)
#     return answer

# ---------- Retriever Creation ----------

def create_retriever_from_df(review_df: pd.DataFrame):
    """
    Converts the review DataFrame into a vector database retriever using FAISS.
    """
    try:
        # Use DataFrameLoader to convert the DataFrame into documents
        loader = DataFrameLoader(review_df)
        review_docs = loader.load()
        logger.info(f"Loaded {len(review_docs)} review documents.")
    except Exception as e:
        logger.exception("Error loading documents from DataFrame: " + str(e))
        review_docs = []
    
    # Create embeddings using a HuggingFace model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # Build the vector store using FAISS
    vectordb = FAISS.from_documents(documents=review_docs, embedding=embeddings)
    retriever = vectordb.as_retriever()
    return retriever

# ---------- Chatbot Chain Setup ----------

def create_qa_chain(retriever) -> RetrievalQA:
    """
    Creates a RetrievalQA chain using an LLM and conversation memory.
    """
    # Initialize conversation memory to track chat history
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,output_key="answer")
    # Initialize the chat LLM (e.g., GPT-4)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.5)
    system_prompt = '''You are a helpful AI assistant for Amazon sellers. 
                            Your job is to analyze product reviews and metadata to answer seller queries.. 
                            Your responses should be clear, concise, and insightful.

                            Relevant Data:
                            {context}

                            Question: {question}
                            Guidelines:
                            - Summarize insights from reviews if applicable.
                            - Avoid including raw review text unless explicitly requested.
                            - Format your response in a readable way.
                            '''

    PROMPT = PromptTemplate(template=system_prompt, input_variables=["context", "question"])
    # Build a RetrievalQA chain using a simple "stuff" chain type
    qa_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory, return_source_documents=True,
        combine_docs_chain_kwargs={'prompt': PROMPT})
    # qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, memory=memory, combine_docs_chain_kwargs={"prompt": PROMPT})
    return qa_chain


def chatbot(asin, user_question):
    try:
        logger.info(f"Processing ASIN: {asin}")
        # Fetch reviews and metadata
        review_df = fetch_reviews(asin)
        meta_df = fetch_metadata(asin)

        if review_df.empty:
            logger.warning(f"No reviews found for ASIN: {asin}")
            return "No review data found for the provided ASIN.", []

        # Create a retriever from the reviews DataFrame
        retriever = create_retriever_from_df(review_df)

        # Create the QA chain using the retriever
        qa_chain = create_qa_chain(retriever)

        # Generate an answer using the QA chain
        answer = qa_chain.invoke({'question': user_question})
        logger.info(f"Generated response: {answer['answer']}")
        # Extract conversation history
        conversation_history = qa_chain.memory.chat_memory.messages
        for msg in qa_chain.memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                role = "User"
            elif isinstance(msg, AIMessage):
                role = "Assistant"
            elif isinstance(msg, SystemMessage):
                role = "System"
            else:
                role = "Unknown"
            content = msg.content

        return answer['answer'] 

    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return f"Error processing query: {str(e)}", []
