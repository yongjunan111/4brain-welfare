// features/chatbot/ChatMessage.tsx
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "./chatbot.types";
import { PolicyCardItem } from "./PolicyCard";

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const policies = message.policies ?? [];

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
      <div className={`flex flex-col gap-3 ${isUser ? "items-end max-w-[80%]" : "flex-1 min-w-0"}`}>
        <div
          className={[
            "rounded-2xl px-3 py-2 text-[15px] leading-relaxed",
            isUser ? "bg-blue-800 text-white" : "bg-gray-100 text-gray-900 w-full",
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

        {!isUser && policies.length > 0 && (
          <div className="w-full space-y-2">
            {policies.map((policy) => (
              <PolicyCardItem key={policy.plcy_no || policy.plcy_nm} policy={policy} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
