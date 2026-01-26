from config import llm
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


messages = [
    HumanMessage(content="Write a complex dp problem using cpp and c and python and java and js")
]

# 3. Invoke the model
# This sends the message to Groq and waits for the response
response = llm.invoke(messages)

print(response.content)