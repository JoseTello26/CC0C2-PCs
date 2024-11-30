import streamlit as st
import requests
from elasticsearch import Elasticsearch

# Streamlit app title
st.title("QA Chat")

# URL of the API endpoint
api_url = "https://mrkite-bertapi.hf.space/answer"

# Create a chat-like interface
if "messages" not in st.session_state:
    st.session_state["messages"] = []

context = ""



# Input boxes for question and context
st.write("## Haz una pregunta:")
question = st.text_input("Pregunta:", key="user_state")



es = Elasticsearch(["https://mrkite-elasticsearch.hf.space"])  # Adjust the host as needed
index_name="textbooks"

response = es.indices.put_settings(
    index=index_name,
    body={
        "index": {
            "highlight.max_analyzed_offset": 2000000
        }
    }
)

query = {
    "query": {
        "match": {
            "markdown": question
        },
        
    },
    "highlight": {
        "type": "unified",
        "fields": {
            "markdown": {
                "fragment_size": 500,  
                "number_of_fragments": 3
            }
        }
    },
}

response = es.search(index="textbooks", body=query)


context_titles = []

for hit in response["hits"]["hits"][:min(3, len(response["hits"]["hits"]))]:
    print("-"*20)
    print(f"Document ID: {hit['_id']}")
    print(f"Score: {hit['_score']}")
    context_titles.append((hit["_source"]["topic"],hit["_score"]))
    for fragment in hit["highlight"]["markdown"]:
        
        context += "\n" + fragment.replace("<em>", "").replace("</em>", "")
        
print(context)
        

def send_question():
    global question
    global context
    if question and context:
        req = {"question": question, "context": context}

        try:
            response = requests.post(api_url, json=req)
            response.raise_for_status()
            result = response.json()

            # Append user input and response to chat history
            st.session_state["messages"].insert(0,
                {"role": "assistant", "content": result.get("answer", "No answer found.")}
            )
            st.session_state["messages"].insert(0, {"role": "user", "content": question})
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error calling API: {e}")
    else:
        st.warning("Please provide both a question and context.")

# Send button
if st.button("Send"):
    send_question()

# Display previous messages
st.write("## Chat History")
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg['content'])
    else:
        with st.chat_message("assistant"):
            st.write(msg['content'])
            st.write("-"*3)
            st.write("Sources:")
            for title, score in context_titles:
                st.write(f"- {title} - Score={score}")


#streamlit run app.py