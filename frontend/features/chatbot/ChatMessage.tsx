// features/chatbot/ChatMessage.tsx
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "./chatbot.types";

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "items-start gap-3"}`}>
      {!isUser && (
        <Image
          src="/logo/welfarecompass.png"
          alt="챗봇 아이콘"
          width={40}
          height={40}
          className="mt-1 h-10 w-10 shrink-0 rounded-full border border-sky-200 bg-white p-1"
        />
      )}
      <div
        className={[
          "max-w-[80%] rounded-2xl px-3 py-2 text-[15px] leading-relaxed",
          isUser ? "bg-blue-800 text-white" : "bg-gray-100 text-gray-900",
        ].join(" ")}
      >
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ ...props }) => (
                <a
                  {...props}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 underline"
                />
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
