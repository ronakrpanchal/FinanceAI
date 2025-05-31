import streamlit as st
import requests
import time

API_ENDPOINT = st.secrets["BACKEND_URL"]

def typewriter_effect(text, delay=0.005, is_markdown=True):
    placeholder = st.empty()
    typed_text = ""
    for char in text:
        typed_text += char
        if is_markdown:
            placeholder.markdown(typed_text, unsafe_allow_html=True)
        else:
            placeholder.write(typed_text)
        time.sleep(delay)

def chatbot(user_id):

    # Set the app title
    st.title("FinSight – AI Financial Strategist 💼")

    # Initialize session state to store chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
        else:
            st.chat_message("assistant").markdown(message["content"])

    # Chat input field
    if prompt := st.chat_input("Ask about budgeting, savings, or financial goals..."):
        # Append user's message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        
        try:
            response = requests.post(
                f"{API_ENDPOINT}/chat",
                json={"user_id": user_id, "query": prompt}
            )
            
            if response.status_code == 200:
                api_response = response.json()
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    message_placeholder.markdown(typewriter_effect(api_response["response"]))
                assistant_response = {
                    "role": "assistant",
                    "content": api_response["response"]
                }
                st.session_state.messages.append(assistant_response)
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

        # # 💬 Simulated assistant response (static demo for now)
        # demo_response = (
        #     "You’re allocating ₹5,000 to **Entertainment**, which is 20% of your income. "
        #     "To optimize savings, reduce this to 10% and redirect the excess to **Emergency Fund**.\n\n"
        #     "Would you like me to save this allocation?"
        # )
        
        # # Display assistant message
        # st.chat_message("assistant").markdown(demo_response)
        
        # # Append simulated assistant response
        # st.session_state.messages.append({
        #     "role": "assistant",
        #     "content": demo_response,
        #     "analysis": {
        #         "category": "Entertainment",
        #         "allocated": 5000,
        #         "recommended": 2500,
        #         "action": "Reduce discretionary spending and shift funds to Emergency Fund."
        #     }
        # })