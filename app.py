# -*- coding: utf-8 -*-
"""
A Flask chatbot that integrates OpenAI Function Calling and Cal.com API.
It can help users book, list, and cancel events via conversation.
"""
import os
import json
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from cal_client import book_event, list_bookings


load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tools = [
    {
        "type": "function",
        "name": "book_event",
        "description": "help me to book a meeting",
        "parameters": {
            "type": "object",
            "properties": {
                "eventTypeId": {"type": "string", "description": "Cal.com event type ID"},
                "start": {"type": "string", "description": "Start time in ISO format (e.g. 2025-10-10T10:00:00Z)"},
                "email": {"type": "string", "description": "Attendee email"},
                "name": {"type": "string", "description": "Attendee name"},
                "location": {"type": "string", "description": "Event location (e.g. Zoom, Google Meet, etc.)"}
            },
            "required": ["eventTypeId", "start", "email"]
        }
    },
    {
        "type": "function",
        "name": "list_bookings",
        "description": "list my bookings",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Attendee email"},
                "name": {"type": "string", "description": "Attendee name"},
            },
            "required": ["email"]
        }
    }
]

def extract_text_from_response(resp):
    texts = []
    out = getattr(resp, "output", [])
    for item in out:
        if hasattr(item, "content") and isinstance(item.content, list):
            for subitem in item.content:
                if hasattr(subitem, "text") and subitem.text:
                    texts.append(subitem.text)
        elif hasattr(item, "text") and item.text:
            texts.append(item.text)
    return "\n".join(texts) if texts else "(no text found)"



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    # 1. 从前端获取输入 — prefer JSON body but accept multiple content types
    data = request.get_json(silent=True) or {}
    if not data:
        # fallback to form or querystring
        data = request.form.to_dict() or request.args.to_dict() or {}

    user_input = (data.get("message") or data.get("text") or "").strip()
    if not user_input:
        return jsonify({"error": "No message received"}), 400

    # Build a minimal input list for the model
    input_list = [{"role": "user", "content": user_input}]

    # Call the model — wrap in try/except so we return JSON on errors
    try:
        response = client.responses.create(
            model="gpt-5",
            tools=tools,
            input=input_list,
        )
    except Exception as e:
        app.logger.exception("OpenAI request failed")
        return jsonify({"error": "model request failed", "detail": str(e)}), 500

    # 保存 function call 输出
    input_list += response.output

    for item in response.output:
        print("item:", item)

        if item.type == "function_call":
            if item.name == "book_event":
                # 不再依赖 status
                try:
                    args = json.loads(item.arguments)
                    print("Function call item:", item)

                    bookresult = book_event(args)

                    # 如果返回 status 不是 success，也处理成错误消息
                    if isinstance(bookresult, dict) and bookresult.get("status") != "success":
                        bookresult_text = f"❌ Failed to book meeting: {bookresult}"
                    else:
                        bookresult_text = f"✅ Booking successful: {bookresult}"

                except Exception as e:
                    bookresult_text = f"❌ Error calling book_event: {e}"

                print("Function call result:", bookresult_text)
                input_list.append({
                    "type": "function_call_output",
                    "call_id": getattr(item, "call_id", None),
                    "output": json.dumps({"bookresult": bookresult_text})
                })

            if item.name == "list_bookings":
                try:
                    args = json.loads(item.arguments)
                    print("Function call item:", item)
                    bookings_result = list_bookings(json.loads(item.arguments))
                    print("Function call result:", bookings_result)

                    if isinstance(bookings_result, dict) and bookings_result.get("status") != "success":
                        bookings_text = f"❌ Failed to list bookings: {bookings_result}"
                    else:
                        bookings_text = "\n".join([f"{b['title']} at {b['start']}" for b in bookings_result.get("data", [])])
                except Exception as e:
                    bookings_text = f"❌ Error calling list_bookings: {e}"

                input_list.append({
                    "type": "function_call_output",
                    "call_id": getattr(item, "call_id", None),
                    "output": json.dumps({"bookings": bookings_text})
                })
        '''
        if item.type == "reasoning":
            input_list.append({
                "type": "reasoning",
                "role": "assistant",
                "content": item.content
            })
        '''
        

            

    # 4. 再次调用模型生成最终回复
    final_response = client.responses.create(
        model="gpt-5",
        instructions="Respond to the user with booking or events information in plain text.",
        tools=tools,
        input=input_list
    )

    # Attempt to extract a useful text reply in a few safe ways
    reply = extract_text_from_response(final_response)
    try:
        # New SDKs often expose `output_text`
        reply = getattr(final_response, "output_text", None)
        if not reply:
            # Some SDKs provide a list-like `output` structure
            out = getattr(final_response, "output", None)
            if isinstance(out, list) and len(out) > 0:
                # try to find the first plain text content
                for item in out:
                    # item may be a dict-like or object
                    content = None
                    if isinstance(item, dict):
                        content = item.get("content") or item.get("text")
                    else:
                        content = getattr(item, "content", None) or getattr(item, "text", None)
                    if content:
                        reply = content
                        break
            # fallback to stringifying the response
        if not reply:
            reply = str(final_response)
    except Exception:
        reply = "(unable to parse model response)"

    return jsonify({"reply": reply})



if __name__ == "__main__":
    app.run(debug=True)
