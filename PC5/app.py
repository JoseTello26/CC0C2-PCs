import streamlit as st
import requests
from elasticsearch import Elasticsearch
import re
from pprint import pp

# Streamlit app title
st.title("QA Chat")

# URL of the API endpoint
api_url = "https://mrkite-bertapi.hf.space/answer"

# Create a chat-like interface
if "messages" not in st.session_state:
    st.session_state["messages"] = []


# Input boxes for question and context
st.write("## Haz una pregunta:")



def accquire_context(question, type_search):
    context = []
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
            "nested": {
                "path": "markdown",
                "query": {
                    "match": {
                        "markdown.content": {
                            "query": question,  # The search query text
                        }
                    }
                },
                "inner_hits": {  # Return detailed inner hit results
                    "highlight": {
                        "type": type_search,
                        "fields": {
                            "markdown.content": {
                                "fragment_size": 500,  # Smaller fragment size
                                "number_of_fragments": 3  # Limit to 3 fragments
                            }
                        }
                    }
                }
            }
        }
    }

    response = es.search(index="textbooks", body=query)


    context_titles = []

    for hit in response["hits"]["hits"][:min(3, len(response["hits"]["hits"]))]:
        print("-"*20)
        print(f"Document ID: {hit['_id']}")
        print(f"Score: {hit['_score']}")
        # context_titles.append((hit["_source"]["topic"],hit["_score"]))
        # pp(hit["inner_hits"])
        context_titles.append((hit["_source"]["topic"], hit["_score"]))
        for inner_hit in hit["inner_hits"]["markdown"]["hits"]["hits"]:
            # pp(inner_hit["_source"])
            

            for fragment in inner_hit["highlight"]["markdown.content"]:
                # pp(fragment)
                fragment = re.sub(r"#.*?(?=\n)","", fragment)
                fragment = re.sub(r"[\n\r]", "", fragment)
                fragment = fragment.replace("<em>", "").replace("</em>", "")
                # print(fragment)
                context.append(fragment)
            
    print(context)
    return context, context_titles
        

def send_question(question, context):
    if question and context:
        req = {"question": question, "context": context}
        #pp(req)
        try:
            response = requests.post(api_url, json=req)
            response.raise_for_status()
            result = response.json()
            
            return result.get("answer", "No answer found.")
            
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error calling API: {e}")
    else:
        st.warning("Please provide both a question and context.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        type_search=["plain", "unified"]
        for t in type_search:
            context, references = accquire_context(prompt, t)
            answer = send_question(prompt, context)
            st.markdown(f"### Type: {t}")
            st.markdown(answer)
            st.markdown("**References:**")
            for r in references:
                st.markdown(f"- {r[0]} \t\t Score: {r[1]}")
            st.markdown("---")
            st.session_state["messages"].append(
                        {"role": "assistant", "content": answer}
                    )
