from flask import Flask, render_template, request, Response, stream_with_context
from flask_cors import CORS  # Import CORS
from dotenv import load_dotenv

import webbrowser
from threading import Timer
import os
from llama_index import (
    ServiceContext,
    VectorStoreIndex,
    SimpleDirectoryReader,
    set_global_service_context,
)
from llama_index.llms import OpenAI
from llama_index.memory import ChatMemoryBuffer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")


# Set up the service context for llama-index with the desired OpenAI model
service_context = ServiceContext.from_defaults(
    llm=OpenAI(model="gpt-4", temperature=0)
)
set_global_service_context(service_context)

# Load the data from the "data" directory
data = SimpleDirectoryReader("data").load_data()

# Create the index
index = VectorStoreIndex.from_documents(data)

# Configure the chat engine with a memory buffer
memory = ChatMemoryBuffer.from_defaults(token_limit=20000)
chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "Act as an experienced risk and financial policy analyst"
        "You are now able to intelligently answer questions about the information you have been provided"
    ),
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    response = chat_engine.stream_chat(user_message)
    buffer = []
    buffer_size = 3

    def generate():
        for token in response.response_gen:
            buffer.append(token)
            if len(buffer) >= buffer_size:
                yield ''.join(buffer)
                buffer.clear()
        if buffer:
            yield ''.join(buffer)

    return Response(stream_with_context(generate()), content_type='text/plain')

def open_browser():
      webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        Timer(1, open_browser).start()
    app.run(debug=True)

