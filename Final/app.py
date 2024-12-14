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

with st.sidebar:
    search_type = st.selectbox(
        "Tipo de búsqueda",
        ("plain", "unified"),
        placeholder="Select contact method..."
    )


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
                                "fragment_size": 800,  # Smaller fragment size
                                "number_of_fragments": 5  # Limit to 3 fragments
                            }
                        }
                    }
                }
            }
        }
    }

    response = es.search(index="textbooks", body=query)


    context_titles = []

    for hit in response["hits"]["hits"][:min(2, len(response["hits"]["hits"]))]:
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
        

def send_question(question, context, threshold=1e-2):
    if question and context:
        req = {"question": question, "context": context, "threshold": threshold}
        #pp(req)
        try:
            response = requests.post(api_url, json=req)
            response.raise_for_status()
            result = response.json()
            print(result.get("score"))
            return result.get("answer", "No se encontró respuesta en el dataset :("), result.get("context", "...")
            
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error calling API: {e}")
    else:
        st.warning("No se encontró contexto con esa pregunta")

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
        context, references = accquire_context(prompt, search_type)
        answer, best_ctx = send_question(prompt, context)
        full_text_response = f"### Type: {search_type}\n\n**Answer:** {answer}\n\n**Source:** \"...{best_ctx}...\""
        st.markdown(full_text_response)
        st.markdown("**References:**")
        for r in references:
            st.markdown(f"- {r[0]} \t\t Score: {r[1]}")
        st.markdown("---")
        st.session_state["messages"].append(
                    {"role": "assistant", "content": full_text_response}
                )
