import React, { useState } from "react";

export default function App() {
  const [messages, setMessages] =
    useState([]);
  const [input, setInput] =
    useState("");
  const [temperature, setTemperature] =
    useState(0.7);
  const [isConcise, setIsConcise] =
    useState(false);
  const [isLoading, setIsLoading] =
    useState(false);

  // A simple static thread_id for this session.
  // In production, generate a UUID or link it to a user session.
  const threadId = "table_1";

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      role: "user",
      content: input,
    };
    setMessages((prev) => [
      ...prev,
      userMessage,
    ]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/chat",
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            user_input: input,
            thread_id: threadId,
            temperature_setting:
              parseFloat(temperature),
            length_instruction:
              isConcise
                ? "Keep your responses very concise, brief, and straight to the point. No fluff."
                : "Provide highly detailed, elaborate, and descriptive resp",
          }),
        },
      );

      const data =
        await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "chef",
          content: data.response,
        },
      ]);
    } catch (error) {
      console.error(
        "Error communicating with backend:",
        error,
      );
      setMessages((prev) => [
        ...prev,
        {
          role: "chef",
          content:
            "Sorry, the kitchen is closed. (Server Error)",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "40px auto",
        fontFamily: "sans-serif",
      }}
    >
      <h2>The AI Chef</h2>

      {/* Controls */}
      <div
        style={{
          padding: "15px",
          background: "#f5f5f5",
          borderRadius: "8px",
          marginBottom: "20px",
        }}
      >
        <label
          style={{
            display: "block",
            marginBottom: "10px",
          }}
        >
          <strong>
            Creativity (Temperature):{" "}
            {temperature}
          </strong>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={temperature}
            onChange={(e) =>
              setTemperature(
                e.target.value,
              )
            }
            style={{
              width: "100%",
              marginTop: "5px",
            }}
          />
        </label>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <input
            type="checkbox"
            checked={isConcise}
            onChange={(e) =>
              setIsConcise(
                e.target.checked,
              )
            }
          />
          <strong>
            Keep it concise?
          </strong>
        </label>
      </div>

      {/* Chat Window */}
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: "8px",
          padding: "20px",
          height: "400px",
          overflowY: "auto",
          marginBottom: "20px",
        }}
      >
        {messages.length === 0 && (
          <p
            style={{
              color: "#888",
              textAlign: "center",
            }}
          >
            Start chatting with the
            Chef!
          </p>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: "15px",
              textAlign:
                msg.role === "user"
                  ? "right"
                  : "left",
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "10px 15px",
                borderRadius: "15px",
                background:
                  msg.role === "user"
                    ? "#007bff"
                    : "#e9ecef",
                color:
                  msg.role === "user"
                    ? "white"
                    : "black",
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}
        {isLoading && (
          <div
            style={{ color: "#888" }}
          >
            The Chef is thinking...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={sendMessage}
        style={{
          display: "flex",
          gap: "10px",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) =>
            setInput(e.target.value)
          }
          placeholder="Ask the chef what to eat..."
          style={{
            flex: 1,
            padding: "10px",
            borderRadius: "4px",
            border: "1px solid #ccc",
          }}
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading}
          style={{
            padding: "10px 20px",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
