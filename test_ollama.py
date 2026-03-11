from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.1:8b")
response = model.invoke("Säg hej på svenska i en mening.")
print(response)