import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Loader2, Cloud } from "lucide-react";
import { api, ChatMessage } from "../utils/api";
import clsx from "clsx";

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";

  return (
    <div className={clsx("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={clsx(
          "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5",
          isUser ? "bg-brand-500/20" : "bg-purple-500/20"
        )}
      >
        {isUser ? (
          <User size={14} className="text-brand-400" />
        ) : (
          <Bot size={14} className="text-purple-400" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={clsx(
          "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-brand-500/15 text-gray-200 rounded-tr-sm"
            : "bg-[#111827] border border-gray-800 text-gray-300 rounded-tl-sm"
        )}
      >
        {msg.content.split("\n").map((line, i) => (
          <p key={i} className={line === "" ? "h-2" : ""}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [starters, setStarters] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getStarters().then((r) => setStarters(r.starters)).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(newMessages, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't connect to the backend. Make sure the API is running and your AWS credentials are configured.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-xl font-semibold text-white">AI Cost Assistant</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Ask questions about your AWS spend in plain English
        </p>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto bg-[#0d1117] border border-gray-800 rounded-xl p-5 space-y-4 mb-4">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <Cloud size={22} className="text-purple-400" />
            </div>
            <div>
              <p className="text-gray-400 font-medium">
                Ask me anything about your AWS costs
              </p>
              <p className="text-gray-600 text-sm mt-1">
                I have access to your live cost data and resource scan results.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full max-w-xl">
              {starters.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left text-sm px-4 py-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 rounded-xl text-gray-400 hover:text-gray-200 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-purple-500/20 flex items-center justify-center mt-0.5">
              <Bot size={14} className="text-purple-400" />
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <Loader2 size={16} className="text-purple-400 animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Why did my costs spike last Tuesday?"
          disabled={loading}
          className="flex-1 bg-[#0d1117] border border-gray-800 focus:border-brand-500/50 outline-none rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-600 transition-colors"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="flex items-center gap-2 px-4 py-3 bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-white text-sm font-medium transition-colors"
        >
          <Send size={15} />
          Send
        </button>
      </form>
    </div>
  );
}
