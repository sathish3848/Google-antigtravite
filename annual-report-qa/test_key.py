import truststore
truststore.inject_into_ssl()

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
reply = llm.invoke("Hello, how are you?")

print(reply.content)
