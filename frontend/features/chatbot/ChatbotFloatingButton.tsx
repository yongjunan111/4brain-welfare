"use client";

import Image from "next/image";
import { useChatbotStore } from "@/stores/chatbot.store";

export function ChatbotFloatingButton() {
    const isOpen = useChatbotStore((s) => s.isOpen);
    const open = useChatbotStore((s) => s.open);

    // 모달이 열려있으면 버튼을 숨김
    if (isOpen) return null;

    return (
        <div className="fixed bottom-3 right-6 z-40 group">
            <div className="pointer-events-none absolute right-full top-1/3 -translate-y-1/2 whitespace-nowrap rounded-full bg-gray-800 px-3 py-1.5 text-xs text-white opacity-0 shadow transition-opacity duration-150 group-hover:opacity-100">
                무엇을 도와드릴까요?
            </div>
            <button
                onClick={open}
                className="relative size-22 overflow-hidden rounded-full cursor-pointer shrink-0"
                aria-label="챗봇 열기"
            >
                <Image
                    src="/mascot/mascot.png"
                    alt="챗봇 열기"
                    fill
                    sizes="88px"
                    className="object-cover"
                />
            </button>
        </div>
    );
}
